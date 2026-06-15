"""
规划器服务

包装 BFS 两阶段路径规划算法。工具图按领域从 DB 加载（多领域改造，期二）。
"""

import logging
from dataclasses import asdict

from pkg.amplicon.planner import plan, PlanningRequest
from app.services.domain_service import DomainService

logger = logging.getLogger(__name__)


class PlannerService:

    @staticmethod
    def plan_workflow(db, domain_id: int, available_inputs: list[str], goal_types: list[str]) -> list[dict]:
        """
        调用 BFS 规划器，返回 top 3 方案列表。
        工具图取自 domain_id 对应领域（verified & active 脚本）。
        每个方案: {id, tool_chain, final_types, goals_reached, goals_missed, score, explanation}
        """
        tools = DomainService.get_domain_tools(db, domain_id)
        request = PlanningRequest(
            available_inputs=available_inputs,
            goal_types=goal_types,
        )

        candidates = plan(tools, request)
        logger.info(f"[PlannerService] domain={domain_id} 规划结果: {len(candidates)} 个方案")

        return [asdict(c) for c in candidates]
