"""
独立单步分析脚本服务（StandaloneScriptService）

Path B 的"模板仓库 + 召回"：管理 standalone 分析模板的【召回】（P2）与【生成+归档】（P3）。

召回（retrieve-then-judge，STANDALONE_ANALYSIS_PLAN.md §4.6）：
  没有召回，归档就是死文件。`_standalone_route` 的第一步就是召回——命中则原样重放
  模板清单 + 复用脚本，未命中/低置信才从头生成并归档。这是 B 闭环的一等公民。

  - 取该域下所有 is_active 的 standalone 模板（tool_id 前缀 standalone-），解析其契约
    （analysis_type + aliases + 数据形态摘要）；基数小（几十种量级）。
  - 一次 LLM 判定：只在高置信【同义匹配】时返回 tool_id；拿不准返回 null
    （宁可重新生成，不要错配）。
  - 无模板 / 未命中 / 低置信 / LLM 不可用 → 返回 None（视为 miss，由上层从头生成）。

模板契约（归档时写入 Script.md_content，JSON）：
  {analysis_type, aliases, data_requirements, params, runtime_hint, user_query}
  召回命中后据此【原样重放】清单，不重新 LLM 生成。

P3 将在此文件追加 generate() / archive()。
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re

import httpx
from sqlalchemy.orm import Session

from app.models import Domain, Script
from config.llm import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL_NAME,
    LLM_CODEGEN_TIMEOUT,
    LLM_PARSER_TIMEOUT,
)

logger = logging.getLogger(__name__)

# 落盘/检索约定
STANDALONE_PREFIX = "standalone-"
STANDALONE_DOMAIN_CODE = "stats"  # 复用 stats 域（id 由 code 解析，不硬编码）
_GENERATED_DIR = "scripts/standalone/generated"  # 相对 backend 根；与 amplicon 隔离
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,48}$")


def _resolve_domain_id(db: Session) -> int | None:
    """解析 standalone 模板归属的领域 id（默认 stats）。无则 None。"""
    d = Domain.where(db, code=STANDALONE_DOMAIN_CODE).first()
    return d.id if d else None


def parse_contract(script: Script) -> dict:
    """从 Script.md_content 解析 standalone 契约 JSON。解析失败返回空契约。"""
    raw = (script.md_content or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


class StandaloneScriptService:
    """独立单步分析模板的召回（P2）/ 生成+归档（P3）。"""

    @staticmethod
    def recall_template(db: Session, content: str) -> dict | None:
        """检索-then-judge：高置信同义匹配 → 返回模板全契约；否则 None。

        返回契约（命中时）：{tool_id, script_id, file_path, analysis_type, aliases,
        data_requirements, params, runtime_hint}。
        """
        if not DASHSCOPE_API_KEY or not (content or "").strip():
            return None

        domain_id = _resolve_domain_id(db)
        if domain_id is None:
            logger.info("[StandaloneRecall] 无 stats 域，跳过召回")
            return None

        scripts = (
            Script.where(db, domain_id=domain_id, is_active=1)
            .filter(Script.tool_id.like(f"{STANDALONE_PREFIX}%"))
            .all()
        )
        if not scripts:
            logger.info("[StandaloneRecall] 无已归档 standalone 模板，miss")
            return None

        # 构造候选清单（tool_id + analysis_type + aliases + 数据摘要）
        candidates = []
        contract_by_tool: dict[str, dict] = {}
        for s in scripts:
            c = parse_contract(s)
            analysis_type = (c.get("analysis_type") or s.name or "").strip()
            aliases = c.get("aliases") or []
            data_req = c.get("data_requirements") or []
            data_summary = "、".join(
                f"{d.get('label','')}（列：{'/'.join(d.get('columns') or []) or '未指定'}）"
                for d in data_req if isinstance(d, dict)
            ) or "（数据要求未记录）"
            candidates.append({
                "tool_id": s.tool_id,
                "analysis_type": analysis_type,
                "aliases": aliases,
                "data_summary": data_summary,
            })
            contract_by_tool[s.tool_id] = {**c, "tool_id": s.tool_id, "script_id": s.id,
                                           "file_path": s.file_path}

        judge = StandaloneScriptService._judge_match(content, candidates)
        match_id = (judge or {}).get("match")
        confidence = (judge or {}).get("confidence", "")
        logger.info(
            f"[StandaloneRecall] judge match={match_id!r} confidence={confidence} "
            f"reason={(judge or {}).get('reason','')!r}"
        )

        # 只在高置信同义匹配时命中
        if match_id and confidence == "high" and match_id in contract_by_tool:
            logger.info(f"[StandaloneRecall] 命中模板 {match_id}，重放清单")
            return contract_by_tool[match_id]

        return None

    @staticmethod
    def _judge_match(content: str, candidates: list[dict]) -> dict | None:
        """一次 LLM 判定用户需求是否与某候选模板同义匹配。

        返回 {match: "<tool_id>"|null, confidence: high|medium|low, reason}。
        LLM 不可用/失败 → None（上层视为 miss）。
        """
        cand_text = "\n".join(
            f"- tool_id={c['tool_id']}：{c['analysis_type']}"
            f"（别名：{' / '.join(c['aliases']) or '无'}；数据：{c['data_summary']}）"
            for c in candidates
        )
        system = (
            "你是生物信息分析平台的【独立分析模板匹配判定器】。判断用户的【分析需求】是否与"
            "下列某个已归档模板【同义】——即做的是同一种分析（只是说法/措辞不同）。\n"
            "候选模板：\n" + cand_text + "\n\n"
            "判定标准：\n"
            "- match：若用户需求与某个模板【同义】（如『生存分析』≈『KM 生存曲线』≈『预后差异』），"
            "返回该 tool_id；否则返回 null。\n"
            "- confidence：high = 高度确信是同一种分析；medium/low = 有疑虑。\n"
            "- **拿不准返回 match=null**（宁可重新生成，也不要把不同分析错配到现成模板）。\n"
            "只输出 JSON：{\"match\": \"<tool_id 或 null>\", \"confidence\": \"high|medium|low\", \"reason\": \"<简短中文>\"}"
        )
        try:
            resp = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": content},
                    ],
                },
                timeout=LLM_PARSER_TIMEOUT,
            )
            resp.raise_for_status()
            data = json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning(f"[StandaloneRecall] 匹配判定失败，视为 miss: {type(e).__name__}: {e}")
            return None

        match = str(data.get("match") or "").strip()
        if match.lower() in ("null", "none", ""):
            match = ""
        confidence = str(data.get("confidence") or "").strip().lower()
        if confidence not in ("high", "medium", "low"):
            confidence = "low"
        reason = str(data.get("reason") or "").strip()
        return {"match": match, "confidence": confidence, "reason": reason}

    # ─── P3：生成 + 归档（自包含成品脚本）──────────────────────────────
    @staticmethod
    def generate_and_archive(
        analysis_type: str, data_requirements: list[dict], params: list[dict],
        runtime_hint: str, content: str, db: Session, user_id: int,
    ) -> dict | None:
        """生成自包含脚本 + 归档成模板（写全契约，供召回重放 + P4 执行）。

        失败返回 None（上层不阻断清单，仅缺归档/复用）。幂等：同 analysis_type 复用。
        """
        gen = StandaloneScriptService._generate(
            analysis_type, data_requirements, params, runtime_hint, content
        )
        if not gen:
            return None
        return StandaloneScriptService._archive(
            gen, analysis_type, data_requirements, params, runtime_hint, content, db, user_id
        )

    @staticmethod
    def _generate(
        analysis_type: str, data_requirements: list[dict], params: list[dict],
        runtime_hint: str, content: str,
    ) -> dict | None:
        """一次 LLM 生成自包含 R/python 脚本。返回 {sh_content, outputs, language, slug, aliases}。"""
        if not DASHSCOPE_API_KEY or not (content or "").strip():
            return None

        runtime = (runtime_hint or "").strip()
        language = "python" if "py" in runtime.lower() else "R"
        lang_hint = "R" if language == "R" else "python"

        # 输入/参数人类可读描述
        in_lines = []
        for d in data_requirements:
            cols = ", ".join(d.get("columns") or []) or "（未指定）"
            in_lines.append(
                f"- {d.get('label')}（key={d.get('key')}, 格式={d.get('format') or '?'}, "
                f"必需={d.get('required')}, 列: {cols}; 说明: {d.get('columns_desc') or ''}）"
            )
        inputs_desc = "\n".join(in_lines) or "（未给定输入要求）"
        param_lines = [
            f"- {p.get('label')}（key={p.get('key')}, 默认={p.get('default')!r}, 可选={p.get('options') or []}）"
            for p in params
        ]
        params_desc = "\n".join(param_lines) or "（无参数）"

        system = (
            f"你是资深生物信息脚本工程师。生成一个**自包含**的 {lang_hint} 脚本，直接完成下述分析："
            "读取给定输入文件（按指定列名/格式）、按参数（默认值）做分析、产出结果文件。\n\n"
            "硬性要求：\n"
            "1. **自包含**：不依赖任何外部平台/类型系统，不做多步流水线串联；一个文件进→文件出。\n"
            "2. **真能跑**：用真实的包与函数（如 R 的 survival/survminer/ggplot2/pheatmap/glmnet；"
            "python 的 pandas/scipy/matplotlib/lifelines/sklearn）。**严禁用 cp/touch/echo 重定向伪造结果**。\n"
            "3. **输入路径走环境变量**：每个输入文件用 `KEY` 大写的环境变量取路径，默认 `input/<key>.<fmt>`：\n"
            "   - R: `CLINICAL_FILE <- Sys.getenv('CLINICAL_FILE', 'input/clinical.tsv')` 然后按列名读；\n"
            "   - python: `CLINICAL_FILE = os.environ.get('CLINICAL_FILE', 'input/clinical.tsv')`。\n"
            "4. **输出到 output/ 目录**（脚本里 `dir.create('output', showWarnings=FALSE)` 或 `os.makedirs('output', exist_ok=True)`）。\n"
            "5. 按给定列名读取；对可选输入（未提供时）优雅跳过，不崩。\n"
            "6. 同时给 slug（小写 ascii 短横线标识，如 survival-km、volcano-plot）与 aliases（中文同义词列表，"
            "用于召回，如 [\"生存分析\",\"生存曲线\",\"KM\",\"预后\"]）。\n\n"
            "只输出 JSON（不要 markdown 代码块）：\n"
            '{"sh_content": "<完整脚本字符串>", '
            '"outputs": [{"filename": "<output/km_curve.pdf>", "desc": "<说明>"}], '
            '"language": "R|python", "slug": "<ascii-slug>", "aliases": ["<中文同义词>", "..."]}'
        )
        user = (
            f"【分析类型】{analysis_type}\n"
            f"【运行时提示】{runtime or lang_hint}\n"
            f"【输入数据要求】\n{inputs_desc}\n\n"
            f"【参数（用默认值）】\n{params_desc}\n\n"
            f"【用户原话】{content}\n\n请生成自包含脚本。"
        )
        try:
            resp = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=LLM_CODEGEN_TIMEOUT,
            )
            resp.raise_for_status()
            data = json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning(f"[StandaloneGen] 生成失败: {type(e).__name__}: {e}")
            return None

        sh = str(data.get("sh_content") or "").strip()
        outputs = [o for o in (data.get("outputs") or []) if isinstance(o, dict)] or []
        language = str(data.get("language") or "").strip().lower() or language
        slug = str(data.get("slug") or "").strip().lower()
        aliases = [str(a).strip() for a in (data.get("aliases") or []) if str(a).strip()]

        # 校验
        if len(sh) < 40:
            logger.warning(f"[StandaloneGen] 脚本过短({len(sh)})，丢弃")
            return None
        real_indicator = ("library(" in sh or "<-" in sh or "read." in sh) if language != "python" \
            else ("import " in sh or "pd." in sh or "plt." in sh or "df" in sh)
        if not real_indicator:
            logger.warning("[StandaloneGen] 脚本缺真实命令标识，丢弃")
            return None
        if not _SLUG_RE.match(slug):
            slug = "gen-" + hashlib.md5(analysis_type.encode("utf-8")).hexdigest()[:10]

        logger.info(f"[StandaloneGen] 生成 {language} 脚本 {len(sh)} 字符, slug={slug}, aliases={aliases}")
        return {"sh_content": sh, "outputs": outputs, "language": language, "slug": slug, "aliases": aliases}

    @staticmethod
    def _archive(
        gen: dict, analysis_type: str, data_requirements: list[dict], params: list[dict],
        runtime_hint: str, content: str, db: Session, user_id: int,
    ) -> dict:
        """落盘脚本 + 写/更新 Script 模板行（全契约存 md_content）。幂等：同 analysis_type 复用。"""
        domain_id = _resolve_domain_id(db)
        language = gen.get("language") or "R"
        ext = "R" if language.startswith("r") else "py"
        slug = gen["slug"]
        tool_id = f"{STANDALONE_PREFIX}{slug}"

        # 幂等：按 analysis_type 找既有模板
        existing = None
        if domain_id:
            for s in Script.where(db, domain_id=domain_id, is_active=1).filter(
                Script.tool_id.like(f"{STANDALONE_PREFIX}%")
            ).all():
                if (parse_contract(s).get("analysis_type") or "").strip() == (analysis_type or "").strip():
                    existing = s
                    break

        if existing:
            target = existing
            tool_id = existing.tool_id
            # 复用原 file_path（可能 ext 不同则用新的）
            file_path = existing.file_path if existing.file_path else f"{_GENERATED_DIR}/{slug}.{ext}"
            reused = True
        else:
            # 新建：tool_id 碰撞（不同 analysis_type 同 slug）→ 加后缀
            if Script.where(db, tool_id=tool_id).first() is not None:
                slug = f"{slug}-{hashlib.md5(analysis_type.encode('utf-8')).hexdigest()[:6]}"
                tool_id = f"{STANDALONE_PREFIX}{slug}"
            file_path = f"{_GENERATED_DIR}/{slug}.{ext}"
            target = Script(
                tool_id=tool_id,
                name=(analysis_type or "独立分析")[:100],
                domain_id=domain_id or 0,
                uploaded_by=user_id,
            )
            reused = False

        # 落盘（相对 backend 根；LF 换行）
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(gen["sh_content"])
        if not os.path.exists(file_path):
            logger.error(f"[StandaloneArchive] 落盘失败: {file_path}")
            return {"tool_id": tool_id, "file_path": file_path, "reused": reused, "aliases": gen["aliases"]}

        # 全契约（召回重放 + P4 执行所需）
        contract = {
            "analysis_type": analysis_type,
            "aliases": gen["aliases"],
            "data_requirements": data_requirements,
            "params": params,
            "runtime_hint": runtime_hint,
            "outputs": gen["outputs"],
            "language": language,
            "user_query": (content or "")[:500],
            "note": "LLM 现生成·独立分析模板",
        }

        target.name = (analysis_type or "独立分析")[:100]
        target.description = f"LLM 现生成·独立分析模板：{analysis_type}"
        target.tool_id = tool_id
        target.category = "独立分析"
        target.file_path = file_path
        target.domain_id = domain_id or 0
        target.md_content = json.dumps(contract, ensure_ascii=False)
        target.inputs = json.dumps([d.get("key") for d in data_requirements], ensure_ascii=False)
        target.outputs = json.dumps(
            [o.get("filename") for o in gen["outputs"] if isinstance(o, dict)], ensure_ascii=False
        )
        target.verified = 1
        target.is_active = 1
        target.uploaded_by = user_id
        target.save(db)

        logger.info(f"[StandaloneArchive] {'复用' if reused else '新建'} {tool_id} -> {file_path}")
        return {
            "tool_id": tool_id,
            "file_path": file_path,
            "reused": reused,
            "aliases": gen["aliases"],
            "outputs": gen["outputs"],
            "language": language,
        }
