"""
领域分流器

判断用户输入属于哪个分析领域，并先做「是不是生信任务」的相关性闸。

策略（classify_with_relevance）：
  1. 关键词唯一高分命中 → 高置信直接命中（省一次 LLM 调用）；
  2. 否则 LLM 相关性判定，给出 domain_code / in_scope / confidence；
  3. 无启用领域、未配 key、超时或解析失败 → uncertain（让上层追问，不硬拒）。

关键点：即使只有一个启用领域也跑相关性判定，不再无条件钦定单库。
"""

import json
import logging

import httpx
from sqlalchemy.orm import Session

from app.models import Domain
from config.llm import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL_NAME,
    LLM_PARSER_TIMEOUT,
)

logger = logging.getLogger(__name__)

AMPLICON_CODE = "amplicon"


def _parse_examples(raw: str) -> list[str]:
    """解析 domains.examples（JSON list[str]），容错返回 list。"""
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if isinstance(data, list):
        return [str(e).strip() for e in data if str(e).strip()]
    return []


class DomainClassifier:
    """领域分流器。

    classify_with_relevance 返回 {domain_id, in_scope, confidence, reason}：
      - in_scope=True                 → 属于某领域，domain_id 给出，可钉领域继续解析/规划；
      - in_scope=False, high          → 明确与生信分析无关（out_of_scope），应友好拒绝、不钉领域；
      - in_scope=False, medium/low/uncertain → 不确定，应追问引导、不钉领域、不硬拒。
    """

    @staticmethod
    def classify(db: Session, content: str) -> int | None:
        """薄封装：返回领域 id（out_of_scope / uncertain 时为 None）。

        兼容旧调用；新流程应直接用 classify_with_relevance 拿到 in_scope/confidence。
        """
        verdict = DomainClassifier.classify_with_relevance(db, content)
        return verdict["domain_id"]

    @staticmethod
    def classify_with_relevance(db: Session, content: str) -> dict:
        """返回 {domain_id, in_scope, confidence, reason}。

        domain_id 可能为 None（无启用领域 / out_of_scope / uncertain）。
        """
        domains = Domain.where(db, is_active=1).order_by(Domain.sort_order.asc()).all()
        if not domains:
            return {
                "domain_id": None,
                "in_scope": False,
                "confidence": "uncertain",
                "reason": "无启用领域",
            }

        # 快路径：唯一关键词高分命中 → 高置信直接命中
        hit = DomainClassifier._keyword_unique_hit(domains, content)
        if hit is not None:
            return {
                "domain_id": hit.id,
                "in_scope": True,
                "confidence": "high",
                "reason": "关键词命中",
            }

        # 原始测序数据 → 归 amplicon（唯一含"从原始数据跑到下游方法"全流程的领域）。
        # LLM 在这条上不可靠（会把"原始数据+PCoA"误判到只做下游的 stats，理由还谎称"未提原始数据"），
        # 故在 LLM 前加可靠安全网。仅当存在 amplicon 域时生效；将来有别的 raw-data 域再细化。
        text_lc = (content or "").lower()
        raw_signals = ["原始数据", "下机数据", "fastq", "双端测序", "单端测序"]
        if any(s in text_lc for s in raw_signals):
            amp = next((d for d in domains if d.code == AMPLICON_CODE), None)
            if amp is not None:
                logger.info(f"[DomainClassifier] 原始数据信号 → 钉 amplicon（安全网，绕过 LLM 误判）")
                return {
                    "domain_id": amp.id,
                    "in_scope": True,
                    "confidence": "high",
                    "reason": "原始测序数据→扩增子全流程领域",
                }

        # LLM 相关性判定（描述由 T1 在导入时填充；单库时唯一候选仍验相关性）
        return DomainClassifier._relevance_llm(domains, content)

    @staticmethod
    def _keyword_unique_hit(domains: list[Domain], content: str) -> Domain | None:
        """关键词得分最高且唯一最高（>0）→ 返回该领域；否则 None。"""
        text = (content or "").lower()
        scored: list[tuple[int, Domain]] = []
        for d in domains:
            kws = [k.strip().lower() for k in (d.keywords or "").split(",") if k.strip()]
            score = sum(1 for k in kws if k and k in text)
            scored.append((score, d))
        if not scored:
            return None
        scored.sort(key=lambda x: x[0], reverse=True)
        top_score, top_d = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0
        if top_score > 0 and second_score < top_score:
            logger.info(f"[DomainClassifier] 关键词唯一命中领域 {top_d.code}")
            return top_d
        return None

    @staticmethod
    def _relevance_llm(domains: list[Domain], content: str) -> dict:
        """LLM 判定输入是否属于某领域，给 domain_code / in_scope / confidence / candidates。

        无 key / 超时 / 解析失败 → uncertain（让 chat 侧追问，不硬拒）。
        candidates：可信候选领域（按可能性排序），供多库低置信时"你是指 A 还是 B"追问（T4）。
        """
        uncertain = {
            "domain_id": None,
            "in_scope": False,
            "confidence": "uncertain",
            "reason": "无法判定（未配置 key / 超时 / 解析失败）",
            "candidates": [],
        }
        if not DASHSCOPE_API_KEY or not (content or "").strip():
            return uncertain

        # 每个库附 1-2 条 example_queries 作 few-shot（T1 生成）
        lines = []
        for d in domains:
            ex_list = _parse_examples(getattr(d, "examples", "") or "")
            ex = "；示例问法：" + " / ".join(ex_list[:2]) if ex_list else ""
            lines.append(f"- {d.code}：{d.name}（{d.description}；关键词：{d.keywords}{ex}）")
        system = (
            "你是生物信息分析平台的领域分流器。判断用户输入是否属于下列任一分析领域，"
            "若是则指出是哪个。\n可选领域：\n"
            + "\n".join(lines)
            + "\n\n只输出 JSON（不要 markdown 代码块或解释）：\n"
            '{"domain_code": "<领域 code，或 none>", '
            '"in_scope": <true|false>, '
            '"confidence": "high|medium|low", '
            '"candidates": ["<可信候选领域 code，按可能性排序，1-3 个；domain_code=none 时可为空>"], '
            '"reason": "<简短中文理由>"}\n'
            "判定标准：\n"
            "- 方法名相同时按【数据类型】区分（关键）：若多个领域都含同一分析方法"
            "（如 PCoA/PCA/随机森林/LEfSe/T检验 等下游方法），以用户已有的数据为准——"
            "用户提到原始测序数据（fastq/fasta/双端/原始数据/下机数据/原始fastq）时，"
            "即使同时点了某个下游方法，也应归入【包含从原始数据跑到该方法的完整流程】的领域，"
            "而不是仅做单步下游分析的领域（后者要求用户已具备计算好的丰度表/特征表/距离矩阵）。\n"
            "- 输入明显属于某领域 → 对应 code、in_scope=true、high；\n"
            "- 输入明显与生物信息分析无关（天气、闲聊、订餐、新闻等）→ "
            "domain_code=\"none\"、in_scope=false、high；\n"
            "- 像是某领域但不够确定 → medium，并把可能的领域都放进 candidates；\n"
            "- 信息太少无法判断 → low（domain_code 可为 none）。"
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
            raw = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)
        except Exception as e:
            logger.warning(f"[DomainClassifier] LLM 相关性判定失败，返回 uncertain：{e}")
            return uncertain

        code = str(data.get("domain_code") or "").strip().strip("`").strip()
        in_scope_raw = data.get("in_scope")
        confidence = str(data.get("confidence") or "").strip().lower()
        reason = str(data.get("reason") or "").strip()
        if confidence not in {"high", "medium", "low"}:
            confidence = "low"

        # 解析 candidates（list 或逗号串）→ 映射到真实领域对象
        candidate_objs = DomainClassifier._map_candidates(domains, data.get("candidates"))

        is_none = (not code) or code.lower() == "none"
        if is_none:
            logger.info(
                f"[DomainClassifier] LLM 判定不属于任何领域 (confidence={confidence})"
            )
            return {
                "domain_id": None,
                "in_scope": False,
                "confidence": confidence,
                "reason": reason or "不属于任何启用领域",
                "candidates": candidate_objs,
            }

        matched = next(
            (d for d in domains if d.code == code or code in d.code or d.code in code),
            None,
        )
        if matched is None:
            logger.warning(f"[DomainClassifier] LLM 返回 code {code!r} 无法匹配领域")
            return {
                "domain_id": None,
                "in_scope": False,
                "confidence": confidence,
                "reason": f"领域 code {code!r} 无法匹配",
                "candidates": candidate_objs,
            }

        # 确保主选在候选首位（disambiguate 列表要含它）
        candidate_objs = DomainClassifier._ensure_first(candidate_objs, matched)

        # code 非空时 in_scope 默认 true（以 LLM 显式输出为准）
        in_scope = True if in_scope_raw is None else bool(in_scope_raw)
        logger.info(
            f"[DomainClassifier] LLM 判定 domain={matched.code} "
            f"in_scope={in_scope} confidence={confidence} candidates={[c['code'] for c in candidate_objs]}"
        )
        return {
            "domain_id": matched.id,
            "in_scope": in_scope,
            "confidence": confidence,
            "reason": reason,
            "candidates": candidate_objs,
        }

    @staticmethod
    def _map_candidates(domains: list[Domain], raw) -> list[dict]:
        """把 LLM 返回的候选 code 列表映射成 [{id,code,name,description}]，去重保序。"""
        if isinstance(raw, str):
            codes = [c.strip() for c in raw.replace("，", ",").split(",") if c.strip()]
        elif isinstance(raw, list):
            codes = [str(c).strip() for c in raw if str(c).strip()]
        else:
            codes = []
        out: list[dict] = []
        seen: set[int] = set()
        for c in codes:
            c = c.strip().strip("`").strip()
            if not c or c.lower() == "none":
                continue
            m = next((d for d in domains if d.code == c or c in d.code or d.code in c), None)
            if m and m.id not in seen:
                seen.add(m.id)
                out.append({
                    "id": m.id,
                    "code": m.code,
                    "name": m.name,
                    "description": (m.description or "").strip(),
                })
        return out

    @staticmethod
    def _ensure_first(candidates: list[dict], primary: Domain) -> list[dict]:
        """确保主选领域在候选列表首位（不在则插入到首位）。"""
        primary_in = any(c["id"] == primary.id for c in candidates)
        if primary_in:
            return [c for c in candidates if c["id"] == primary.id] + \
                   [c for c in candidates if c["id"] != primary.id]
        return [{
            "id": primary.id,
            "code": primary.code,
            "name": primary.name,
            "description": (primary.description or "").strip(),
        }] + candidates
