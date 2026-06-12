"""
从 scripts/Amplicon/reference/*.md 提取工具、输入、输出元数据，
生成 neo4j-docker-compose/data.json 供 init.py 导入 Neo4j。

图模型：
  (IO)-[:input]->(Tool)
  (Tool)-[:output]->(IO)
IO 节点按 description（文件描述）共享：同一个描述出现多次时合并为一个节点，
因此一个工具的 output 可以是另一个工具的 input。
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# 让脚本可以导入 backend 包
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from pkg.amplicon.amplicon_tools import get_all_tools
from pkg.amplicon.script_registry import TOOL_SCRIPT_CALLS


REFERENCE_DIR = BACKEND_ROOT / "scripts" / "Amplicon" / "reference"
OUTPUT_FILE = BACKEND_ROOT / "neo4j-docker-compose" / "data.json"


def parse_basic_info_table(text: str) -> dict:
    """解析 基本信息 的 2 列表格。"""
    result = {}
    section = re.search(r"##\s*基本信息\s*\n(.*?)(?=##\s|$)", text, re.S)
    if not section:
        return result
    for line in section.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "---" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) != 2:
            continue
        key, value = cols
        key = re.sub(r"\*+", "", key).strip()
        result[key] = value
    return result


def parse_io_table(text: str, section_name: str) -> list[dict]:
    """解析 输入/输出 的 5 或 6 列表格。"""
    rows = []
    section = re.search(rf"##\s*{re.escape(section_name)}\s*\n(.*?)(?=##\s|$)", text, re.S)
    if not section:
        return rows

    for line in section.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "---" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if not cols or "描述" in cols[1] or "文件" in cols[0]:
            continue
        if len(cols) == 5:
            rows.append({
                "filename": strip_backticks(cols[0]),
                "description": cols[1],
                "format": cols[2],
                "omics": cols[3],
                "species": cols[4],
                "example": "",
            })
        elif len(cols) >= 6:
            rows.append({
                "filename": strip_backticks(cols[0]),
                "description": cols[1],
                "format": cols[2],
                "omics": cols[3],
                "species": cols[4],
                "example": cols[5] if len(cols) > 5 else "",
            })
    return rows


def strip_backticks(s: str) -> str:
    return s.strip("`").strip()


def normalize_tool_name(name: str) -> str:
    """把 tool_name 转成 registry 短 id 形式（下划线改连字符）。"""
    return name.strip().lower().replace("_", "-")


def normalize_description(desc: str) -> str:
    """用于 IO 节点去重的描述标准化。"""
    return re.sub(r"\s+", "", desc.strip())


def io_node_id(desc: str) -> str:
    """根据描述生成唯一且稳定的 IO 节点 ID。"""
    norm = normalize_description(desc)
    safe = re.sub(r"[^\w一-鿿]", "_", norm)[:80]
    return f"io-{safe}"


def build_registry_lookups():
    registry_tools = get_all_tools()
    by_short_id = {}
    for t in registry_tools:
        short_id = t.id.replace("amp-", "")
        by_short_id[short_id] = t
    return registry_tools, by_short_id


def parse_md_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    basic = parse_basic_info_table(text)
    if not basic:
        return None

    return {
        "tool_name": basic.get("Tool Name", ""),
        "title": path.stem,
        "description": basic.get("Description", ""),
        "scope": basic.get("适用范围", ""),
        "estimated_time": basic.get("估算机时", ""),
        "quotation_score": basic.get("报价分数", ""),
        "inputs": parse_io_table(text, "输入"),
        "outputs": parse_io_table(text, "输出"),
    }


def resolve_tool_id(parsed: dict, filename_stem: str, by_short_id: dict) -> str:
    """根据 MD 里的 tool_name 或文件名匹配 registry tool_id。"""
    candidates = [
        normalize_tool_name(parsed["tool_name"]),
        normalize_tool_name(filename_stem),
    ]
    if "_" in filename_stem:
        candidates.append(normalize_tool_name(filename_stem.split("_", 1)[1]))

    for cand in candidates:
        if cand in by_short_id:
            return by_short_id[cand].id
    return f"md-{parsed['tool_name'] or filename_stem}"


def parse_numeric(value: str):
    """尝试把 估算机时/报价分数 转成数字，失败保留原字符串。"""
    if value is None:
        return None
    cleaned = re.sub(r"[^\d.\-]", "", value)
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return value


def main():
    registry_tools, by_short_id = build_registry_lookups()
    script_map = dict(TOOL_SCRIPT_CALLS)

    tool_nodes = []
    io_profiles = defaultdict(lambda: {
        "filenames": set(),
        "formats": set(),
        "omics": set(),
        "species": set(),
        "examples": set(),
    })
    relationships = []
    relationship_keys = set()

    def add_relationship(from_id: str, to_id: str, rel_type: str):
        key = (from_id, to_id, rel_type)
        if key in relationship_keys:
            return
        relationship_keys.add(key)
        relationships.append({
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            "properties": {},
        })

    md_files = sorted(REFERENCE_DIR.glob("step*.md"))
    print(f"Found {len(md_files)} reference MD files.")

    for md_path in md_files:
        parsed = parse_md_file(md_path)
        if not parsed:
            print(f"Skipping {md_path.name}: no basic info table.")
            continue

        tool_id = resolve_tool_id(parsed, md_path.stem, by_short_id)
        registry_tool = by_short_id.get(tool_id.replace("amp-", ""))
        category = registry_tool.category if registry_tool else ""
        script_path = script_map.get(tool_id).script_path if tool_id in script_map else ""

        tool_nodes.append({
            "id": tool_id,
            "label": "Tool",
            "properties": {
                "id": tool_id,
                "name": parsed["tool_name"],
                "title": parsed["title"],
                "description": parsed["description"],
                "scope": parsed["scope"],
                "estimated_time": parse_numeric(parsed["estimated_time"]),
                "quotation_score": parse_numeric(parsed["quotation_score"]),
                "category": category,
                "script_path": script_path,
            },
        })

        for row in parsed["inputs"]:
            desc = row["description"]
            if not desc:
                continue
            io_id = io_node_id(desc)
            profile = io_profiles[io_id]
            profile["description"] = desc
            profile["filenames"].add(row["filename"])
            profile["formats"].add(row["format"])
            profile["omics"].add(row["omics"])
            profile["species"].add(row["species"])
            profile["examples"].add(row["example"])
            add_relationship(io_id, tool_id, "input")

        for row in parsed["outputs"]:
            desc = row["description"]
            if not desc:
                continue
            io_id = io_node_id(desc)
            profile = io_profiles[io_id]
            profile["description"] = desc
            profile["filenames"].add(row["filename"])
            profile["formats"].add(row["format"])
            profile["omics"].add(row["omics"])
            profile["species"].add(row["species"])
            profile["examples"].add(row["example"])
            add_relationship(tool_id, io_id, "output")

    io_nodes = []
    for io_id, profile in io_profiles.items():
        io_nodes.append({
            "id": io_id,
            "label": "IO",
            "properties": {
                "description": profile["description"],
                "filenames": sorted([v for v in profile["filenames"] if v]),
                "formats": sorted([v for v in profile["formats"] if v]),
                "omics": sorted([v for v in profile["omics"] if v]),
                "species": sorted([v for v in profile["species"] if v]),
                "examples": sorted([v for v in profile["examples"] if v]),
            },
        })

    data = {
        "nodes": tool_nodes + io_nodes,
        "relationships": relationships,
    }

    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(tool_nodes)} Tool nodes, {len(io_nodes)} IO nodes, "
          f"{len(relationships)} relationships to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
