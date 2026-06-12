"""
基于 Neo4j 图数据求解分析工具执行路径。

把图一次性加载到内存，用 BFS 搜索从给定输入 IO 到输出 IO 的可执行路径。
可执行的含义：路径上每个 Tool 的所有 input 都已经被满足（来自初始输入或前面 Tool 的输出）。
"""

import os
from collections import defaultdict, deque
from typing import Iterable

from neo4j import GraphDatabase


class Neo4jPlanService:
    """
    从 Neo4j 读取 Tool / IO 关系图，求解可执行分析路径。

    用法：
        paths = Neo4jPlanService.find_paths(
            input_descriptions=["均一化 ASV 表"],
            output_descriptions=["DCA 排序图（SVG 格式）"],
            max_paths=3,
        )
        # paths = [["amp-dca"], ...]
    """

    _graph: dict | None = None
    _driver_instance = None

    @staticmethod
    def _get_driver():
        if Neo4jPlanService._driver_instance is None:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            username = os.getenv("NEO4J_USERNAME", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "bioflow123")
            Neo4jPlanService._driver_instance = GraphDatabase.driver(uri, auth=(username, password))
        return Neo4jPlanService._driver_instance

    @staticmethod
    def _load_graph() -> dict:
        """从 Neo4j 加载全图并构建内存索引。"""
        graph = {
            "tools": set(),
            "ios": set(),
            "tool_inputs": defaultdict(set),   # tool_id -> {io_id}
            "tool_outputs": defaultdict(set),  # tool_id -> {io_id}
            "io_props": {},                    # io_id -> {description, ...}
            "tool_props": {},                  # tool_id -> {name, ...}
        }

        driver = Neo4jPlanService._get_driver()
        with driver.session() as session:
            # 先加载所有节点
            for record in session.run("MATCH (n) RETURN n"):
                node = record["n"]
                node_id = node["id"]
                if "Tool" in node.labels:
                    graph["tools"].add(node_id)
                    graph["tool_props"][node_id] = dict(node)
                elif "IO" in node.labels:
                    graph["ios"].add(node_id)
                    graph["io_props"][node_id] = dict(node)

            # 再加载所有关系
            for record in session.run("MATCH (a)-[r]->(b) RETURN a.id AS a, type(r) AS t, b.id AS b"):
                rel_type = record["t"]
                a = record["a"]
                b = record["b"]
                if rel_type == "input":
                    # IO -> Tool
                    graph["tool_inputs"][b].add(a)
                elif rel_type == "output":
                    # Tool -> IO
                    graph["tool_outputs"][a].add(b)

        return graph

    @staticmethod
    def _ensure_graph() -> dict:
        if Neo4jPlanService._graph is None:
            Neo4jPlanService._graph = Neo4jPlanService._load_graph()
        return Neo4jPlanService._graph

    @classmethod
    def refresh_graph(cls) -> None:
        """当 Neo4j 数据发生变化时调用，刷新内存缓存。"""
        cls._graph = cls._load_graph()

    @staticmethod
    def find_paths(
        input_descriptions: Iterable[str],
        output_descriptions: Iterable[str],
        max_paths: int = 3,
        max_depth: int = 15,
    ) -> list[list[str]]:
        """
        从输入 IO 集合出发，搜索能够产生输出 IO 集合的可执行工具路径。

        Args:
            input_descriptions: 初始可用的 IO 描述列表（支持部分匹配，CONTAINS）
            output_descriptions: 目标输出 IO 描述列表（支持部分匹配，CONTAINS）
            max_paths: 最多返回几条路径
            max_depth: 路径最大长度（Tool 数量），防止爆搜

        Returns:
            list[list[str]]: 每个元素是一条工具 ID 路径，按长度从短到长排序
        """
        graph = Neo4jPlanService._ensure_graph()

        # 把描述匹配到 io_id
        start_ios = set()
        target_ios = set()
        for io_id, props in graph["io_props"].items():
            desc = props.get("description", "")
            if any(d in desc for d in input_descriptions):
                start_ios.add(io_id)
            if any(d in desc for d in output_descriptions):
                target_ios.add(io_id)

        if not start_ios or not target_ios:
            return []

        # BFS 状态：(available_ios, used_tools, path_tools)
        queue = deque([(frozenset(start_ios), frozenset(), [])])
        visited = set()
        paths: list[list[str]] = []

        while queue and len(paths) < max_paths:
            available_ios, used_tools, path_tools = queue.popleft()

            # 状态去重：used_tools 决定了 available_ios，所以用 used_tools 即可
            if used_tools in visited:
                continue
            visited.add(used_tools)

            # 如果目标已经产生，记录路径（要求至少执行了一个 tool），并不再扩展这条路径
            if path_tools and (target_ios & available_ios):
                paths.append(path_tools.copy())
                if len(paths) >= max_paths:
                    break
                continue

            if len(path_tools) >= max_depth:
                continue

            # 找到所有可执行的 tool（未使用且所有 input 都已满足）
            for tool_id in graph["tools"] - used_tools:
                required_inputs = graph["tool_inputs"][tool_id]
                if required_inputs.issubset(available_ios):
                    new_available = available_ios | graph["tool_outputs"][tool_id]
                    new_used = used_tools | {tool_id}
                    new_path = path_tools + [tool_id]
                    queue.append((new_available, new_used, new_path))

        return paths[:max_paths]

    @staticmethod
    def find_paths_with_details(
        input_descriptions: Iterable[str],
        output_descriptions: Iterable[str],
        max_paths: int = 3,
        max_depth: int = 15,
    ) -> list[dict]:
        """
        与 find_paths 相同，但返回每条路径的详细信息（工具名称、输入输出等）。
        """
        graph = Neo4jPlanService._ensure_graph()
        tool_id_paths = Neo4jPlanService.find_paths(
            input_descriptions, output_descriptions, max_paths, max_depth
        )

        results = []
        for tool_ids in tool_id_paths:
            tools = []
            for tid in tool_ids:
                props = graph["tool_props"].get(tid, {})
                tools.append({
                    "id": tid,
                    "name": props.get("name", ""),
                    "description": props.get("description", ""),
                    "category": props.get("category", ""),
                    "script_path": props.get("script_path", ""),
                })
            results.append({
                "tools": tools,
                "tool_ids": tool_ids,
                "length": len(tool_ids),
            })
        return results
