"""
常识意图代理（IntentAgent）

一次 LLM 推理，从【通用生物信息常识】判断用户描述是否已足够确定一个可执行的生信任务：
- 够 → 抽 available_inputs / goal_types（类型 ID 仅作"翻译"，理解过程不查表）；
- 不够 → questions[]：一次问全所有"不定就跑偏"的关键问题。

取代旧"解析器抽类型ID + route_decision 按ID有无选预设追问"两步。意图识别不靠
关键词→预设问题映射，也不靠类型菜单驱动提问——理解与提问基于生信一般常识；
类型词表仅在"够意图"时作翻译目标。失败兜底为通用澄清（绝不替用户默认数据形态，
规避"默认双端"，见 review F1）。
"""

from __future__ import annotations

import json
import logging

import httpx
from sqlalchemy.orm import Session

from app.models import Domain
from app.services.domain_service import DomainService
from config.llm import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL_NAME,
    LLM_PARSER_TIMEOUT,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
【首要规则，高于一切】用户**明确声明拥有的数据**就是唯一入口，直接抽成对应类型 ID\
（单端原始→FASTQ_SINGLE，双端原始→FASTQ_PAIR）。**严禁追问"你有没有更下游的处理产物\
（丰度表 / 距离矩阵 / 已去噪的 ASV 等）"**——那是替下游操心，不归你管。只要用户已说明\
【数据形态】+【分析目标】，就 sufficient=true 直接抽取，不要因为"从原始数据到目标还要好几步"\
而降级或追问。下游能否实现由别的模块判断。

你是生物信息分析平台的【意图理解代理】。基于通用生物信息分析常识，判断用户描述是否已足够\
确定一个可执行的生信分析任务。

你会得到：
- 该领域能做什么（大白话描述）
- 该领域可识别的数据类型词表（type_id：含义）—— 仅用于把已理解的意图"翻译"成可规划的\
类型 ID，不要用它限定你的理解或提问。

严格输出 JSON（不要 markdown 代码块、不要解释）：
{
  "sufficient": true | false,
  "questions": ["...", "..."],
  "available_inputs": ["TYPE_ID", ...],
  "goal_types": ["TYPE_ID", ...],
  "reasoning": "..."
}

字段规则：
- sufficient=true：用户已清楚说明【数据形态】与【分析目标】，足以确定一条分析流程。\
此时填 available_inputs（用户拥有的数据）和 goal_types（想要的结果），questions 留空 []。\
available_inputs / goal_types 必须用词表内的 type_id。
- sufficient=false：存在"不定就会导致完全不同流程"的缺口。此时把所有该问的关键问题一次\
列全到 questions（例如：数据是什么形态？原始数据是单端还是双端？要不要去引物？目标具体是\
哪种多样性/差异分析？），不要挤牙膏分多轮；available_inputs 留空（除非某项已完全确定），\
goal_types 可填已能确定的部分。\
questions 必须用用户能懂的大白话（中文）表述，**绝对不要在里面出现 type_id 内部代号**\
（如 FASTQ_SINGLE、FEATURE_TABLE、PCOA_PLOT、DIST_MATRIX 等），只说人话概念。

判定要点（基于生信常识，不是查词表）：
- **你的职责只是理解用户意图并抽取类型 ID，不负责判断"平台能否从该数据做到该目标"——\
那是下游规划器/能力缺口判定的事。** 所以用户明确说了什么数据，就抽什么；哪怕看起来要从原始数据\
跑很多步，也不要为此降级 sufficient 或追问"你是不是已有处理好的表"。用户说原始数据就是原始数据。
- **数据形态→类型ID 硬映射（用户明确说了就照此抽，不要追问是否是别的形态）：**\
单端原始测序数据/单端fastq → FASTQ_SINGLE；双端原始测序数据/R1R2/双端fastq → FASTQ_PAIR；\
已处理丰度表/ASV表 → ASV_TABLE_EVEN 或 RELATIVE_ABUNDANCE；已算好的距离矩阵 → DIST_MATRIX。
- 凡是"不定就会跑偏"的关键决策（测序布局、分析方法选型）【且用户没提】→ sufficient=false，一次问全。
- 能合理默认的细节参数（截断阈值、线程数等）不要问。
- 不要重复追问用户已在发言中明确给出的信息（已说单/双端就不要再问数据格式；已点名距离/方法就不要再问选型）。
- 用户已明确【数据形态】+【分析目标】→ sufficient=true 直接抽取；次要选项未指定用常规默认。
- 抽类型 ID 时严格用词表内 ID，词表没有的不要硬造；拿不准就归入 sufficient=false 并提问。

示例（few-shot，仿此判定）：
- 「我有单端原始数据做 PCoA」→ sufficient=true, available_inputs=["FASTQ_SINGLE"], goal_types=["PCOA_PLOT"]
- 「我有双端原始数据做 PCoA」→ sufficient=true, available_inputs=["FASTQ_PAIR"], goal_types=["PCOA_PLOT"]
- 「我有原始数据做 PCoA」（没说单/双端）→ sufficient=false, questions=["原始数据是单端还是双端测序？"]
- 「我有相对丰度表做 LEfSe」→ sufficient=true, available_inputs=["RELATIVE_ABUNDANCE"], goal_types=["LEFSE_RESULT"]
"""


# 兜底问题（LLM 不可用时）：只问"数据/目标"两个开放问题，绝不替用户默认数据形态。
_FALLBACK_QUESTIONS = [
    "你目前有什么类型的数据？（例如：原始测序数据、ASV 表、距离矩阵等）",
    "你想获得什么样的分析结果？（例如：物种组成、多样性、差异分析、PCoA 等）",
]


def _fallback(reason: str) -> dict:
    return {
        "sufficient": False,
        "questions": list(_FALLBACK_QUESTIONS),
        "available_inputs": [],
        "goal_types": [],
        "reasoning": reason,
        "fallback": True,
    }


def _format_vocab(vocab: list[dict]) -> tuple[str, set[str]]:
    inputs = [t for t in vocab if t.get("is_uploadable")]
    goals = [t for t in vocab if not t.get("is_uploadable")]

    def _fmt(items: list[dict]) -> str:
        return "\n".join(f"- {t['type_id']}：{t['label']}" for t in items) or "（无）"

    text = (
        "可上传输入类型（用户可能拥有的数据）：\n" + _fmt(inputs)
        + "\n\n分析目标类型（用户可能想要的结果）：\n" + _fmt(goals)
    )
    return text, {t["type_id"] for t in vocab}


class IntentAgent:
    """意图识别代理：一次常识推理输出 sufficient/questions/类型ID。"""

    @staticmethod
    def understand(db: Session, domain: Domain, content: str, history_dicts: list[dict] | None = None) -> dict:
        """返回 {sufficient, questions, available_inputs, goal_types, reasoning, fallback}。"""
        if not DASHSCOPE_API_KEY or not (content or "").strip():
            return _fallback("意图代理未配置或输入为空")

        try:
            vocab = DomainService.get_type_vocab(db, domain.id)
            vocab_text, valid_ids = _format_vocab(vocab)
        except Exception as e:
            logger.warning(f"[IntentAgent] 读取领域词表失败: {e}")
            return _fallback("无法读取领域词表")

        capability = (domain.description or "").strip() or domain.name or "生物信息分析"

        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history_dicts:
            for msg in history_dicts[-20:]:
                if msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg.get("content", "")})

        user_payload = (
            f"【领域能力】{capability}\n\n"
            f"【数据类型词表（仅作翻译用）】\n{vocab_text}\n\n"
            f"【用户本次发言】\n{content}\n\n"
            f"请判断信息是否足够，并按规则输出 JSON。"
        )
        messages.append({"role": "user", "content": user_payload})

        try:
            resp = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": messages,
                },
                timeout=LLM_PARSER_TIMEOUT,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)
        except Exception as e:
            logger.warning(f"[IntentAgent] LLM 调用失败，走兜底: {type(e).__name__}: {e}")
            return _fallback("意图代理 LLM 调用失败")

        return IntentAgent._normalize(data, valid_ids)

    @staticmethod
    def _normalize(data: dict, valid_ids: set[str]) -> dict:
        sufficient = bool(data.get("sufficient", False))
        questions = [str(q).strip() for q in (data.get("questions") or []) if str(q).strip()]
        available = [str(t).strip() for t in (data.get("available_inputs") or []) if str(t).strip()]
        goals = [str(t).strip() for t in (data.get("goal_types") or []) if str(t).strip()]
        reasoning = str(data.get("reasoning") or "").strip()

        avail_valid = [t for t in available if t in valid_ids]
        goal_valid = [t for t in goals if t in valid_ids]
        dropped = [t for t in (available + goals) if t not in valid_ids]
        if dropped:
            logger.warning(f"[IntentAgent] 丢弃词表外类型 ID: {dropped}")

        # 判 sufficient 但缺关键边（available 或 goal 空）→ 降级为追问，避免空规划。
        if sufficient and (not avail_valid or not goal_valid):
            logger.info(
                f"[IntentAgent] sufficient 但缺 available/goal，降级追问 "
                f"(avail={avail_valid}, goal={goal_valid})"
            )
            sufficient = False
            if not questions:
                questions = list(_FALLBACK_QUESTIONS)

        logger.info(
            f"[IntentAgent] sufficient={sufficient} questions={len(questions)} "
            f"available={avail_valid} goal={goal_valid}"
        )
        return {
            "sufficient": sufficient,
            "questions": questions,
            "available_inputs": avail_valid,
            "goal_types": goal_valid,
            "reasoning": reasoning,
            "fallback": False,
        }

    # ─── 能力缺口判定（Phase 2）──────────────────────────────
    @staticmethod
    def classify_capability_gap(db: Session, domain_id: int, available: list[str], goals: list[str], content: str) -> dict:
        """规划找不到路径时，判断这是不是"合理生信任务、只是平台缺工具"的缺口。

        返回 {plausible: bool, missing_link: str}。LLM 不可用/失败 → plausible=False（保守，不误提议生成）。
        """
        if not DASHSCOPE_API_KEY:
            return {"plausible": False, "missing_link": ""}

        try:
            domain = Domain.find(db, domain_id)
            vocab = DomainService.get_type_vocab(db, domain_id)
        except Exception as e:
            logger.warning(f"[CapabilityGap] 读取领域失败: {e}")
            return {"plausible": False, "missing_link": ""}

        label = {t["type_id"]: t["label"] for t in vocab}
        avail_desc = "、".join(label.get(t, t) for t in available) or "（未明确）"
        goal_desc = "、".join(label.get(t, t) for t in goals) or "（未明确）"
        capability = (domain.description if domain else "").strip() or (domain.name if domain else "生物信息分析")

        system = (
            "你是生物信息分析平台的【能力缺口判定器】。用户想做某个分析，但平台现有工具图里找不到"
            "从【用户拥有的数据】到【想要的分析目标】的路径。请基于通用生物信息常识判断：这是不是一个"
            "【合理的、符合生信常识的分析任务，只是平台恰好没有对应的现成工具】？\n"
            "- plausible=true：数据→目标在生信上是成立的常见任务（例如单端扩增子去噪→PCoA、"
            "宏基因组拼接→功能预测），只是平台没装这条链上的某个工具。\n"
            "- plausible=false：数据与目标在生信上不搭配/自相矛盾，或根本不是生信任务"
            "（例如『用 fastq 预测天气』『用物种组成表做基因组拼接』）。\n"
            "只输出 JSON：{\"plausible\": true|false, \"missing_link\": \"<缺的环节，大白话，如 单端原始数据→ASV特征表/去噪>\"}"
        )
        user = (
            f"【领域能力】{capability}\n"
            f"【用户拥有的数据】{avail_desc}\n"
            f"【想要的分析目标】{goal_desc}\n"
            f"【用户原话】{content}\n\n"
            f"请判定。"
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
                        {"role": "user", "content": user},
                    ],
                },
                timeout=LLM_PARSER_TIMEOUT,
            )
            resp.raise_for_status()
            data = json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning(f"[CapabilityGap] LLM 判定失败，保守判 not-plausible: {type(e).__name__}: {e}")
            return {"plausible": False, "missing_link": ""}

        plausible = bool(data.get("plausible", False))
        missing = str(data.get("missing_link") or "").strip()
        logger.info(f"[CapabilityGap] plausible={plausible} missing_link={missing!r}")
        return {"plausible": plausible, "missing_link": missing}
