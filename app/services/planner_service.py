"""
规划器服务

包装 BFS 两阶段路径规划算法。
"""

import logging
from dataclasses import asdict

from pkg.amplicon.amplicon_tools import get_all_tools
from pkg.amplicon.planner import plan, PlanningRequest

logger = logging.getLogger(__name__)


class PlannerService:

    _tools = None

    @classmethod
    def _get_tools(cls):
        if cls._tools is None:
            cls._tools = get_all_tools()
        return cls._tools

    @staticmethod
    def plan_workflow(available_inputs: list[str], goal_types: list[str]) -> list[dict]:
        """
        调用 BFS 规划器，返回 top 3 方案列表。
        每个方案: {id, tool_chain, final_types, goals_reached, goals_missed, score, explanation}
        """
        tools = PlannerService._get_tools()
        request = PlanningRequest(
            available_inputs=available_inputs,
            goal_types=goal_types,
        )

        candidates = plan(tools, request)
        logger.info(f"[PlannerService] 规划结果: {len(candidates)} 个方案")

        return [asdict(c) for c in candidates]
