"""
工具现生成服务（ToolGenesisService）—— Phase 3

能力缺口被用户确认后，基于【通用生物信息常识】当场生成一个【单步工具级】脚本
（与 cutadapt/dada2 同构，不是把整条任务包圆的大脚本），校验它能串进既有流水线、
能被编排器执行，然后落盘 .sh + 写 Script 行（verified=1, is_active=1）+ 清工具图缓存，
使其立即进入规划器可用工具图。

核心原则（见 SMART_CLARIFY_TOOLGEN_PLAN.md §0.3 / §3.1）：
- 不预设生成什么工具。LLM 在运行时按常识决定（单端 DADA2 只是众多可能产物之一）。
- 平台只规定【结构契约 + 串链/执行约束】，不替 LLM 选好工具。
- 串链不变式（§3.3）：新工具的每个输出必须被至少一个既有下游工具消费，或是用户目标类型。
  否则注册前拒收。
- 执行模型约束：现有编排器对 cutadapt/flash/frags-qc 之外的 per-sample 工具会 raise。
  故 prompt 引导 LLM 优先生成【非 per-sample / 吃 manifest】形态。
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess

import httpx
from sqlalchemy.orm import Session

from app.models import Script, Domain
from app.services.domain_service import DomainService
from config.llm import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL_NAME,
    LLM_CODEGEN_TIMEOUT,
)

logger = logging.getLogger(__name__)

# 仓库内落盘根目录（app/services/ → ../../ → backend 根 → scripts/Amplicon/generated）
_GENERATED_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "Amplicon", "generated")
)
# .sh few-shot 风格参考（双端 dada2 文档，让 LLM 类比出单端版）
_DADA2_REF = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "Amplicon", "reference", "step3_dada2.md")
)

# tool_id 命名约束（与既有 amp-* 工具一致）
_TOOL_ID_RE = re.compile(r"^amp-[a-z0-9]+(-[a-z0-9]+)*$")


SYSTEM_PROMPT = """\
你是生物信息分析平台的【脚本工程师】。平台在某个分析任务上发现了能力缺口——\
用户想做某个【合理的、符合生信常识的分析】，但平台现有工具图里找不到从【用户拥有的数据】\
到【想要的目标】的路径。你的任务是：基于通用生物信息常识，判断这个缺口需要什么样的\
【单步】工具来补，然后生成它的 bash 脚本 + I/O 契约。

【硬约束，必须遵守】
1. 只生成【一个单步工具】（与 cutadapt/dada2 同构），不要拼整条流水线、不要写多步串联。
2. tool_id 形如 `amp-<短名>`（小写字母/数字/连字符，如 amp-dada2-se）。
3. inputs / outputs 必须用我给你的【类型词表】里的 type_id（大写蛇形，如 FASTQ_SINGLE、\
FEATURE_TABLE）。词表里没有的不要硬造。
4. 【串链不变式 + 完整性】outputs 里的【每一个】类型都必须从我给的【可选输出类型集合】里\
选（既有下游工具能消费的类型 ∪ 用户目标类型），选集合外的会被拒收。此外 outputs 要【足够\
开启到达用户目标的下游链路】——参照参考文档里同类工具的完整输出集合（如去噪类工具通常同时\
产出代表序列 FEATURE_SEQS 与特征表 FEATURE_TABLE 两类），不要只给一个无法继续推进到目标的\
中间产物。注册后会校验"从用户数据经你的工具能否到达目标"，到达不了会被拒收。
5. inputs 应能消费【用户拥有的数据】（我给你的 available 类型）或其一步衍生。
6. 【执行形态】优先生成【非 per-sample、一次性吃 manifest 处理全部样本】的工具——\
即 per_sample=false，且 call_params 里用一个 data_type="_MANIFEST" 的参数接收样本清单。\
（平台编排器当前只能调度这种形态；per-sample 生成工具会被拒收。）
7. .sh 脚本要求：`#!/bin/bash` 开头 + `set -euo pipefail`；用 getopts 或 case 解析参数；\
核心只调用真实工具命令（如 qiime/cutadapt 等），【禁止用 cp/mkdir/touch/占位注释伪造输出】；\
产出的文件名必须与 call_outputs 的 filename 完全一致。

严格输出 JSON（不要 markdown 代码块、不要解释）：
{
  "sh_content": "<完整 bash 脚本字符串>",
  "contract": {
    "tool_id": "amp-...",
    "name": "<中文工具名>",
    "category": "<分类，如 核心分析/质量控制/数据预处理>",
    "inputs": ["TYPE_ID", ...],
    "outputs": ["TYPE_ID", ...],
    "call_params": [
      {"flag": "-m", "data_type": "_MANIFEST", "required": true},
      {"flag": "-t", "data_type": "_CONFIG", "default": "0", "required": false}
    ],
    "call_outputs": [
      {"data_type": "FEATURE_TABLE", "filename": "featureTable.biom"}
    ],
    "per_sample": false
  }
}

call_params 的 data_type：真实数据类型用词表 type_id；特殊参数用 _MANIFEST(样本清单)、\
_CONFIG(可配置数值/字符串)、_PRIMER_F/_PRIMER_R(引物)、_METADATA、_GROUP_LIST 等。
"""


class ToolGenesisService:
    """现生成单步工具 + 校验 + 落盘 + 录入脚本库。"""

    @staticmethod
    def generate_and_register(
        db: Session,
        domain_id: int,
        offer: dict,
        user_id: int,
        content: str,
    ) -> dict:
        """生成并注册补缺口工具。

        offer = {"available": [...], "goals": [...], "missing_link": "..."}
        返回 {ok, tool_id, script_id, name, reused, reason}。
        ok=False 时 reason 给出拒收/失败原因（不抛异常，由调用方决定如何回复用户）。
        """
        if not DASHSCOPE_API_KEY:
            return {"ok": False, "reason": "未配置 DASHSCOPE_API_KEY，无法现生成脚本"}

        available = offer.get("available") or []
        goals = offer.get("goals") or []
        missing_link = offer.get("missing_link") or ""

        try:
            domain = Domain.find(db, domain_id)
            vocab = DomainService.get_type_vocab(db, domain_id)
        except Exception as e:
            logger.error(f"[ToolGenesis] 读取领域/词表失败: {e}")
            return {"ok": False, "reason": f"读取领域数据失败: {e}"}

        # 串链合法输出集 = 既有下游工具输入并集 ∪ 用户目标类型
        existing_tools = DomainService.get_domain_tools(db, domain_id)
        downstream_inputs: set[str] = set()
        for t in existing_tools:
            downstream_inputs.update(t.inputs)
        legal_outputs = sorted(downstream_inputs | set(goals))
        valid_ids = {t["type_id"] for t in vocab}

        # 1) LLM 现场生成
        try:
            system, user = ToolGenesisService._build_prompt(
                domain, available, goals, missing_link, content, vocab, legal_outputs
            )
            data = ToolGenesisService._llm_generate(system, user)
        except Exception as e:
            logger.error(f"[ToolGenesis] LLM 生成失败: {type(e).__name__}: {e}")
            return {"ok": False, "reason": f"生成调用失败: {e}"}

        sh_content = str(data.get("sh_content") or "").strip()
        contract = data.get("contract") or {}
        if not sh_content or not isinstance(contract, dict):
            return {"ok": False, "reason": "生成结果缺少 sh_content 或 contract"}

        # 2) 契约 + 串链校验（不过则拒收，不落盘不注册）
        try:
            ToolGenesisService._validate_contract(contract, valid_ids, legal_outputs, available)
        except ValueError as e:
            logger.warning(f"[ToolGenesis] 契约校验拒收: {e}\ncontract={contract}")
            return {"ok": False, "reason": f"生成的工具不满足串链/结构约束: {e}"}

        # sh_content 头部粗检（落盘前）
        if "#!/bin/bash" not in sh_content:
            return {"ok": False, "reason": "生成的脚本缺 #!/bin/bash 头"}

        tool_id = contract["tool_id"]

        # 3) 幂等：该 domain 下已有同 tool_id 的启用脚本 → 复用，不重写
        existing = (
            Script.where(db, domain_id=domain_id, tool_id=tool_id, is_active=1, verified=1)
            .first()
        )
        if existing:
            logger.info(f"[ToolGenesis] tool_id={tool_id} 已存在 (script_id={existing.id})，复用")
            return {
                "ok": True,
                "tool_id": tool_id,
                "script_id": existing.id,
                "name": existing.name,
                "reused": True,
                "reason": "",
            }

        # 4) 落盘 + 语法粗检
        os.makedirs(_GENERATED_DIR, exist_ok=True)
        sh_path = os.path.join(_GENERATED_DIR, f"{tool_id}.sh")
        try:
            with open(sh_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(sh_content if sh_content.endswith("\n") else sh_content + "\n")
        except Exception as e:
            logger.error(f"[ToolGenesis] 落盘失败: {e}")
            return {"ok": False, "reason": f"脚本落盘失败: {e}"}

        passed, note = ToolGenesisService._check_syntax(sh_path)
        if not passed:
            logger.warning(f"[ToolGenesis] bash -n 语法不过，拒收: {note}")
            try:
                os.remove(sh_path)
            except OSError:
                pass
            return {"ok": False, "reason": f"生成的脚本语法有误: {note}"}

        # 5) 写 Script 行 + 清缓存
        script = ToolGenesisService._persist(
            db, domain_id, contract, sh_content, user_id, missing_link, content
        )
        DomainService.invalidate(domain_id)

        # 6) 注册后路径校验：available → goals 必须能规划出路径，否则该工具接不上目标
        #    （串链不变式只保证 output 被消费，不保证到达 goal）→ 清理拒收，不留残缺工具
        from app.services.planner_service import PlannerService  # 延迟 import 避免循环依赖
        if not PlannerService.plan_workflow(db, domain_id, available, goals):
            logger.warning(
                f"[ToolGenesis] tool_id={tool_id} 注册后仍规划不出 {available}→{goals}，清理拒收"
            )
            try:
                script.delete(db)
            except Exception as e:
                logger.warning(f"[ToolGenesis] 软删残缺脚本失败: {e}")
            try:
                os.remove(sh_path)
            except OSError:
                pass
            DomainService.invalidate(domain_id)
            return {
                "ok": False,
                "reason": f"生成的工具（{tool_id}）无法接通到目标 {goals}，可能输出类型不完整，请重试或换说法",
            }

        logger.info(
            f"[ToolGenesis] 已生成并注册 tool_id={tool_id} script_id={script.id} "
            f"({sh_path}, syntax_note={note or 'ok'})"
        )
        return {
            "ok": True,
            "tool_id": tool_id,
            "script_id": script.id,
            "name": contract.get("name") or tool_id,
            "reused": False,
            "reason": "",
        }

    # ─── prompt 构造 ───────────────────────────────────────────
    @staticmethod
    def _build_prompt(
        domain: Domain | None,
        available: list[str],
        goals: list[str],
        missing_link: str,
        content: str,
        vocab: list[dict],
        legal_outputs: list[str],
    ) -> tuple[str, str]:
        label_of = {t["type_id"]: t["label"] for t in vocab}
        vocab_text = "\n".join(f"- {t['type_id']}：{t['label']}" for t in vocab) or "（无）"
        legal_text = "、".join(f"{lid}（{label_of.get(lid, lid)}）" for lid in legal_outputs) or "（无）"
        avail_text = "、".join(f"{a}（{label_of.get(a, a)}）" for a in available) or "（未明确）"
        goal_text = "、".join(f"{g}（{label_of.get(g, g)}）" for g in goals) or "（未明确）"
        capability = (domain.description if domain else "").strip() or (domain.name if domain else "生物信息分析")

        fewshot = ToolGenesisService._load_fewshot()

        user = (
            f"【领域能力】{capability}\n\n"
            f"【用户拥有的数据】{avail_text}\n"
            f"【想要的分析目标】{goal_text}\n"
            f"【缺的环节（Phase 2 给出）】{missing_link or '（未明确，请按常识判断）'}\n"
            f"【用户原话】{content}\n\n"
            f"【类型词表（inputs/outputs 只能用这里的 type_id）】\n{vocab_text}\n\n"
            f"【可选输出类型集合（outputs 每一项都必须从这里选——这些是既有下游工具能消费或用户目标的类型）】\n{legal_text}\n\n"
            f"【同族脚本参考（双端 DADA2 的文档，请类比其 manifest/参数/输出风格，"
            f"生成补这个缺口的单步工具，不要照抄双端逻辑）】\n{fewshot}\n\n"
            f"【重要】你的工具输出必须能开启一条经既有工具到达【{goal_text}】的下游链路。"
            f"参照参考文档，同类工具通常输出多个类型（代表序列 + 特征表等），请输出完整集合，"
            f"不要只给单个中间产物，否则下游断链、到达不了目标。\n\n"
            f"请判断这个缺口需要什么单步工具，并生成其 bash 脚本 + I/O 契约 JSON。"
        )
        return SYSTEM_PROMPT, user

    @staticmethod
    def _load_fewshot() -> str:
        try:
            with open(_DADA2_REF, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"[ToolGenesis] 读取 few-shot 参考 {_DADA2_REF} 失败: {e}")
            return "（参考文档不可用）"

    # ─── LLM 调用 ──────────────────────────────────────────────
    @staticmethod
    def _llm_generate(system: str, user: str) -> dict:
        codegen_timeout = max(LLM_CODEGEN_TIMEOUT, 300)
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
            timeout=httpx.Timeout(codegen_timeout, connect=30.0),
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        logger.info(f"[ToolGenesis] LLM 生成返回 {len(raw)} 字符")
        return json.loads(raw)

    # ─── 契约 + 串链校验（§5 自检清单）────────────────────────
    @staticmethod
    def _validate_contract(
        contract: dict,
        valid_ids: set[str],
        legal_outputs: list[str],
        available: list[str],
    ) -> None:
        """不满足则 raise ValueError。"""
        tool_id = str(contract.get("tool_id") or "").strip()
        if not _TOOL_ID_RE.match(tool_id):
            raise ValueError(f"tool_id 非法：{tool_id!r}（需形如 amp-<短名>）")

        name = str(contract.get("name") or "").strip()
        if not name:
            raise ValueError("name 为空")

        inputs = contract.get("inputs")
        outputs = contract.get("outputs")
        if not isinstance(inputs, list) or not inputs:
            raise ValueError("inputs 非空列表")
        if not isinstance(outputs, list) or not outputs:
            raise ValueError("outputs 非空列表")

        for t in inputs:
            if t not in valid_ids:
                raise ValueError(f"input 类型 {t!r} 不在词表内")
        # inputs 至少有一个能接上用户拥有的数据（available）——否则规划器无根
        if available and not (set(inputs) & set(available)):
            raise ValueError(f"inputs {inputs} 与用户拥有的数据 {available} 无交集，无法接上")

        legal_set = set(legal_outputs)
        for t in outputs:
            if t not in valid_ids:
                raise ValueError(f"output 类型 {t!r} 不在词表内")
            if t not in legal_set:
                raise ValueError(
                    f"output 类型 {t!r} 既无既有下游工具消费，也非用户目标（串链不变式不满足）"
                )

        # call_params 结构
        params = contract.get("call_params")
        if not isinstance(params, list) or not params:
            raise ValueError("call_params 非空列表")
        for p in params:
            if not isinstance(p, dict) or not p.get("flag") or not p.get("data_type"):
                raise ValueError(f"call_params 项缺 flag/data_type: {p}")

        # call_outputs 结构 + data_type 必须在 outputs 里
        couts = contract.get("call_outputs")
        if not isinstance(couts, list) or not couts:
            raise ValueError("call_outputs 非空列表")
        out_types = set(outputs)
        for o in couts:
            if not isinstance(o, dict) or not o.get("data_type") or not o.get("filename"):
                raise ValueError(f"call_outputs 项缺 data_type/filename: {o}")
            if o["data_type"] not in out_types:
                raise ValueError(f"call_outputs.data_type {o['data_type']!r} 不在 outputs 中")

        # 执行形态：禁止 per-sample（编排器当前无法调度，见 §3.1）
        if bool(contract.get("per_sample")):
            raise ValueError("per_sample=true 的工具当前无法被编排器调度，请生成吃 manifest 的非 per-sample 形态")

    # ─── 语法粗检 ─────────────────────────────────────────────
    @staticmethod
    def _check_syntax(sh_path: str) -> tuple[bool, str]:
        """bash -n 语法检查。bash 不可用时不阻断（放行 + 备注）。返回 (passed, note)。"""
        try:
            r = subprocess.run(
                ["bash", "-n", sh_path],
                capture_output=True, text=True, timeout=15,
            )
        except FileNotFoundError:
            return True, "bash 不可用，跳过语法检查"
        except Exception as e:
            return True, f"语法检查异常已跳过: {type(e).__name__}"
        if r.returncode == 0:
            return True, ""
        return False, (r.stderr.strip() or f"bash -n 退出码 {r.returncode}")

    # ─── 落盘 + 注册 ──────────────────────────────────────────
    @staticmethod
    def _persist(
        db: Session,
        domain_id: int,
        contract: dict,
        sh_content: str,
        user_id: int,
        missing_link: str,
        content: str,
    ) -> Script:
        inputs = contract["inputs"]
        outputs = contract["outputs"]
        params = contract["call_params"]
        couts = contract["call_outputs"]
        tool_id = contract["tool_id"]

        desc = (
            f"[LLM 现生成] 补缺口：{missing_link or '能力缺口'}。"
            f"输入: {inputs}；输出: {outputs}。用户原话: {content[:80]}"
        )
        script = Script(
            name=contract.get("name") or tool_id,
            description=desc,
            folder_id=0,  # generated 脚本不挂分类文件夹，靠 description 标注来源
            tool_id=tool_id,
            category=contract.get("category") or "核心分析",
            version="1.0.0",
            file_path=f"Amplicon/generated/{tool_id}.sh",  # 相对 $AMPLICON_ROOT
            md_content="",
            inputs=json.dumps(inputs, ensure_ascii=False),
            outputs=json.dumps(outputs, ensure_ascii=False),
            md_inputs="",
            md_outputs="",
            runtime=8,
            cost=14.4,
            weight=len(outputs),
            verified=1,
            is_active=1,
            uploaded_by=user_id,
            verified_by=user_id,
            domain_id=domain_id,
            call_params=json.dumps(params, ensure_ascii=False),
            call_outputs=json.dumps(couts, ensure_ascii=False),
            per_sample=0,  # 已在 _validate_contract 拒收 per-sample
        )
        script.save(db)
        return script
