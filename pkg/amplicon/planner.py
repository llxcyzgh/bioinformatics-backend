"""
两阶段路径规划求解器

阶段1 (BFS core): 从已有输入类型出发，搜索到能产生最多目标类型的中间状态
阶段2 (attach):   从中间状态出发，挂接所有输入已满足的终端工具
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from pkg.amplicon.amplicon_tools import ToolDef, DATA_TYPE_NAMES


@dataclass
class PlanningRequest:
    goal_types: list[str]
    available_inputs: list[str]
    max_depth: int = 10
    top_n: int = 3


@dataclass
class WorkflowCandidate:
    id: str
    tool_chain: list[dict]
    final_types: list[str]
    goals_reached: list[str]
    goals_missed: list[str]
    score: float
    explanation: str


def plan(tools: list[ToolDef], request: PlanningRequest) -> list[WorkflowCandidate]:
    if not request.goal_types or not request.available_inputs:
        return []

    tool_map = {t.id: t for t in tools}
    goal_set = set(request.goal_types)

    # ─── Phase 1: BFS to find core paths ────────────────────
    results: list[tuple[set[str], list[str]]] = []
    visited: set[str] = set()
    explored = 0
    MAX_EXPLORED = 8000

    queue: list[tuple[set[str], list[str]]] = [
        (set(request.available_inputs), [])
    ]

    while queue and explored < MAX_EXPLORED:
        types, chain_ids = queue.pop(0)
        explored += 1

        reached = [g for g in request.goal_types if g in types]
        missed = [g for g in request.goal_types if g not in types]

        if reached:
            results.append((types, chain_ids))
            if not missed:
                continue

        if len(chain_ids) >= request.max_depth:
            continue

        for tool in tools:
            if tool.id in chain_ids:
                continue
            if not all(i in types for i in tool.inputs):
                continue
            new_outputs = [o for o in tool.outputs if o not in types]
            if not new_outputs:
                continue

            new_types = types | set(tool.outputs)
            key = ",".join(sorted(new_types))
            if key in visited:
                continue
            visited.add(key)

            queue.append((new_types, chain_ids + [tool.id]))

    # ─── Phase 2: Attach terminal tools ──────────────────────
    final_results: list[WorkflowCandidate] = []

    for types, chain_ids in results:
        chain_set = set(chain_ids)
        attachable: list[str] = []
        for tool in tools:
            if tool.id in chain_set:
                continue
            if not all(i in types for i in tool.inputs):
                continue
            if any(o in goal_set for o in tool.outputs):
                attachable.append(tool.id)

        full_chain = chain_ids + sorted(attachable)

        all_types = set(types)
        for tid in attachable:
            t = tool_map[tid]
            all_types |= set(t.outputs)

        goals_reached = [g for g in request.goal_types if g in all_types]
        goals_missed = [g for g in request.goal_types if g not in all_types]

        final_results.append(_build_candidate(
            len(final_results), full_chain, tool_map,
            sorted(all_types), goals_reached, goals_missed,
        ))

    final_results.sort(
        key=lambda c: (c.goals_missed == [], c.score),
        reverse=True,
    )

    seen_chains: set[str] = set()
    deduped: list[WorkflowCandidate] = []
    for c in final_results:
        chain_key = ",".join(t["id"] for t in c.tool_chain)
        if chain_key not in seen_chains:
            seen_chains.add(chain_key)
            deduped.append(c)

    return deduped[: request.top_n]


def _build_candidate(
    index: int,
    chain_ids: list[str],
    tool_map: dict[str, ToolDef],
    final_types: list[str],
    goals_reached: list[str],
    goals_missed: list[str],
) -> WorkflowCandidate:
    chain_tools = [tool_map[tid] for tid in chain_ids if tid in tool_map]
    total = max(len(goals_reached) + len(goals_missed), 1)
    score = round(len(goals_reached) / total * 10 - len(chain_ids) * 0.03, 2)

    step_names = " → ".join(t.name for t in chain_tools)
    if not goals_missed:
        explanation = f"完整方案（{len(chain_tools)}步）：{step_names}"
    else:
        missed_names = "、".join(DATA_TYPE_NAMES.get(g, g) for g in goals_missed)
        explanation = f"部分方案（{len(chain_tools)}步）：{step_names}\n未达成目标：{missed_names}"

    return WorkflowCandidate(
        id=f"wf-{index + 1}",
        tool_chain=[{"id": t.id, "name": t.name, "category": t.category} for t in chain_tools],
        final_types=final_types,
        goals_reached=goals_reached,
        goals_missed=goals_missed,
        score=score,
        explanation=explanation,
    )
