"""
领域分流器

根据用户描述判断任务属于哪个分析领域。
策略：仅一个启用领域直接命中 → 关键词命中 → LLM 分类 → amplicon 兜底。
"""

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


class DomainClassifier:

    @staticmethod
    def classify(db: Session, content: str) -> int | None:
        """返回领域 id；无启用领域时返回 None。"""
        domains = Domain.where(db, is_active=1).order_by(Domain.sort_order.asc()).all()
        if not domains:
            return None

        # 仅一个启用领域：直接命中，省 LLM 调用
        if len(domains) == 1:
            return domains[0].id

        # 关键词命中：得分最高且唯一最高
        text = (content or "").lower()
        scored: list[tuple[int, Domain]] = []
        for d in domains:
            kws = [k.strip().lower() for k in (d.keywords or "").split(",") if k.strip()]
            score = sum(1 for k in kws if k and k in text)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored[0][0] > 0 and scored[1][0] < scored[0][0]:
            logger.info(f"[DomainClassifier] 关键词命中领域 {scored[0][1].code}")
            return scored[0][1].id

        # LLM 分类
        return DomainClassifier._classify_llm(db, content, domains)

    @staticmethod
    def _classify_llm(db: Session, content: str, domains: list[Domain]) -> int:
        fallback = DomainClassifier._fallback(db, domains)
        if not DASHSCOPE_API_KEY or not (content or "").strip():
            return fallback

        lines = [
            f"- {d.code}：{d.name}（{d.description}；关键词：{d.keywords}）"
            for d in domains
        ]
        system = (
            "你是生物信息分析平台的领域分流器。根据用户描述判断它属于下面哪个分析领域。"
            "只输出对应领域的代码（code），不要任何解释或标点。\n可选领域：\n"
            + "\n".join(lines)
        )
        try:
            resp = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": content},
                    ],
                },
                timeout=LLM_PARSER_TIMEOUT,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip().strip("`").strip()
            for d in domains:
                if d.code == raw or d.code in raw:
                    logger.info(f"[DomainClassifier] LLM 分类为 {d.code}")
                    return d.id
            logger.warning(f"[DomainClassifier] LLM 返回无法匹配：{raw!r}")
        except Exception as e:
            logger.warning(f"[DomainClassifier] LLM 分类失败，回退兜底：{e}")
        return fallback

    @staticmethod
    def _fallback(db: Session, domains: list[Domain]) -> int:
        amp = Domain.where(db, code=AMPLICON_CODE).first()
        return amp.id if amp else domains[0].id
