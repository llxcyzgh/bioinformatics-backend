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
- 凡是"不定就会跑偏"的关键决策（测序布局、数据预处理选项、分析方法选型）缺失 → sufficient=false，一次问全。
- 能合理默认的细节参数（截断阈值、线程数等）不要问。
- 像一个懂生信的人那样提问：聚焦"会影响流程走向"的关键点。
- 抽类型 ID 时严格用词表内 ID，词表没有的不要硬造；拿不准就归入 sufficient=false 并提问。
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
                    "temperature": 0.1,
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
