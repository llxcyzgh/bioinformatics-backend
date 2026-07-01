"""
规划器服务

包装 BFS 两阶段路径规划算法。工具图按领域从 DB 加载（多领域改造，期二）。
"""

import json
import logging
from dataclasses import asdict

from pkg.amplicon.planner import plan, PlanningRequest
from pkg.amplicon.script_registry import TOOL_SCRIPT_CALLS  # noqa: F401  (保留导入兼容；per_sample 已改读 DB)from app.services.domain_service import DomainService
from app.models.script import Script

logger = logging.getLogger(__name__)


class PlannerService:

    @staticmethod
    def plan_workflow(db, domain_id: int, available_inputs: list[str], goal_types: list[str]) -> list[dict]:
        """
        调用 BFS 规划器，返回 top 3 方案列表。
        工具图取自 domain_id 对应领域（verified & active 脚本）。
        每个方案: {id, tool_chain, final_types, goals_reached, goals_missed, score, explanation}
        tool_chain 每项已富化真实展示属性（version/runtime/cost/weight/inputs/outputs/valid_*）。
        """
        tools = DomainService.get_domain_tools(db, domain_id)
        request = PlanningRequest(
            available_inputs=available_inputs,
            goal_types=goal_types,
        )

        candidates = plan(tools, request)
        logger.info(f"[PlannerService] domain={domain_id} 规划结果: {len(candidates)} 个方案")

        return [PlannerService._enrich(db, domain_id, asdict(c)) for c in candidates]

    @staticmethod
    def _enrich(db, domain_id: int, candidate: dict) -> dict:
        """给候选 tool_chain 每项补上真实 Script 展示属性（版本/耗时/成本/输入输出）。"""
        tool_ids = {
            t["id"] for t in candidate.get("tool_chain", [])
            if isinstance(t, dict) and t.get("id")
        }
        attr_by_tool: dict[str, Script] = {}
        if tool_ids:
            rows = (
                Script.where(db, domain_id=domain_id, verified=1, is_active=1)
                .filter(Script.tool_id.in_(tool_ids))
                .all()
            )
            attr_by_tool = {s.tool_id: s for s in rows}

        for t in candidate.get("tool_chain", []):
            if not isinstance(t, dict) or not t.get("id"):
                continue
            s = attr_by_tool.get(t["id"])
            if s is None:
                continue
            t["version"] = s.version or "1.0.0"
            t["runtime"] = s.runtime or 0
            t["cost"] = s.cost or 0.0
            t["weight"] = s.weight or 0
            t["inputs"] = json.loads(s.inputs or "[]")
            t["outputs"] = json.loads(s.outputs or "[]")
            t["valid_from"] = s.valid_from or ""
            t["valid_until"] = s.valid_until or ""
            t["params"] = json.loads(s.call_params or "[]")
            # per_sample 标志（cutadapt/flash/frags_qc=True）：供前端路径图画"按样本并行分支"。
            # 读 DB 的 Script.per_sample（backfill 时从 ScriptCallDef 写入），不直接依赖静态注册表。
            t["per_sample"] = bool(s.per_sample)

        return candidate
