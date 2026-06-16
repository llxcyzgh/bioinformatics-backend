"""
确定性 .md 脚本说明解析器

客户的每个 .sh 都配了一份结构化 .md（基本信息/输入/输出/参数说明表格），
是脚本的"完整描述"。这里把 .md 确定性地解析成建图与运行需要的字段，
不依赖 LLM。.sh 仅用于执行，不参与解析。

解析产出（与 Script 列对齐）：
  name         <- 首个 H1 标题
  tool_name    <- 基本信息 / Tool Name（用于 tool_id slug）
  description  <- 基本信息 / Description
  runtime      <- 基本信息 / 估算机时（"8.0 小时" → 480 分钟，int）
  cost         <- 基本信息 / 报价分数（float）
  inputs       <- 输入表「文件名」列（JSON list[str]，用于建图连线）
  outputs      <- 输出表「文件名」列（JSON list[str]）
  call_params  <- 参数说明表（JSON list[{flag,data_type,required,default}]）
  call_outputs <- 由 outputs 派生（JSON list[{data_type,filename}]）
"""

from __future__ import annotations

import re
from typing import Optional


# ─── 低层工具 ───────────────────────────────────────────────

def _strip_cell(s: str) -> str:
    """去掉表格单元的 markdown 装饰：`*`、反引号、首尾空白。"""
    s = s.strip().strip("|").strip()
    s = s.replace("`", "")
    # 去掉 **加粗**
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    return s.strip()


def _split_headers(md: str) -> list[tuple[int, str, list[str]]]:
    """把 markdown 按 `^#+ title` 切成 (级别, 标题, 正文行) 列表。"""
    sections: list[tuple[int, str, list[str]]] = []
    cur_level = 0
    cur_title = ""
    cur_body: list[str] = []

    def flush():
        if cur_title:
            sections.append((cur_level, cur_title, cur_body))

    for line in md.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            cur_level = len(m.group(1))
            cur_title = m.group(2).strip()
            cur_body = []
        else:
            cur_body.append(line)
    flush()
    return sections


def _find_section(sections, *titles) -> Optional[list[str]]:
    """找首个标题包含任一关键词的 section，返回其正文行。"""
    needles = [t.lower() for t in titles]
    for _level, title, body in sections:
        tl = title.lower()
        if any(n in tl for n in needles):
            return body
    return None


def _parse_table(lines: list[str]) -> list[list[str]]:
    """从一段正文里抽出 markdown 表格的「数据行」（跳过分隔行）。"""
    rows: list[list[str]] = []
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue
        # 分隔行：|---|---|
        if re.match(r"^\|[\s:|-]+$", s):
            continue
        cells = [_strip_cell(c) for c in s.split("|")]
        # split 会在首尾产生空串，去掉
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        rows.append(cells)
    # 第一个 | 行是表头（紧跟在它后面的是 |---| 分隔行，已跳过），丢掉
    return rows[1:] if rows else []


def _kv_table(rows: list[list[str]]) -> dict[str, str]:
    """两列表格 → {左列: 右列}（用于「基本信息」）。"""
    out: dict[str, str] = {}
    for row in rows:
        if len(row) >= 2:
            out[row[0].lower().strip()] = row[1].strip()
    return out


# ─── 字段解析 ───────────────────────────────────────────────

def _parse_runtime(raw: str) -> int:
    """'8.0 小时' → 480；'30 分钟' → 30；'0' → 0。单位默认分钟。"""
    if not raw:
        return 0
    m = re.search(r"([\d.]+)", raw)
    if not m:
        return 0
    try:
        val = float(m.group(1))
    except ValueError:
        return 0
    if re.search(r"小时|hour|hr|h\b", raw):
        return int(round(val * 60))
    return int(round(val))


def _parse_cost(raw: str) -> float:
    if not raw:
        return 0.0
    m = re.search(r"([\d.]+)", raw)
    try:
        return float(m.group(1)) if m else 0.0
    except ValueError:
        return 0.0


def _clean_filename(cell: str) -> str:
    """输入/输出文件名：去掉反引号、首尾空白、以及末尾括号注释。"""
    s = _strip_cell(cell)
    # 去掉行末示例括注，如 'manifest.tsv (示例...)'
    s = re.sub(r"\s*\(.*\)$", "", s).strip()
    return s


def _infer_data_type(flag: str, default: Optional[str], example: str) -> str:
    """根据默认值/示例推断参数数据类型。"""
    sample = (default or example or "").strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", sample):
        return "int" if "." not in sample else "float"
    if sample and (sample.endswith("/") or re.search(r"\.[a-zA-Z0-9]{1,5}$", sample)):
        return "file"
    return "string"


def _parse_flag(cell: str) -> str:
    """'-m, --manifest' → '-m'（取首个 flag）。"""
    s = _strip_cell(cell)
    if not s:
        return ""
    return s.split(",")[0].strip()


def _parse_bool(cell: str) -> bool:
    s = _strip_cell(cell).lower()
    return s in {"是", "必需", "必填", "true", "yes", "✅", "y", "required"}


def _parse_params(rows: list[list[str]]) -> list[dict]:
    """
    参数说明表，列约定（顺序敏感）：
      参数 | 说明 | 必需 | 默认值 | 示例
    """
    params: list[dict] = []
    for row in rows:
        if len(row) < 2:
            continue
        flag = _parse_flag(row[0])
        if not flag.startswith("-"):
            continue  # 跳过表头/非参数行
        required = _parse_bool(row[2]) if len(row) > 2 else True
        default_raw = row[3] if len(row) > 3 else ""
        default = None if _strip_cell(default_raw) in {"", "-", "—", "无"} else _strip_cell(default_raw)
        example = row[4] if len(row) > 4 else ""
        params.append({
            "flag": flag,
            "data_type": _infer_data_type(flag, default, example),
            "required": bool(required),
            "default": default,
        })
    return params


# ─── 主入口 ─────────────────────────────────────────────────

def parse_md(md_text: str) -> dict:
    """确定性解析 .md 文本 → 字段字典。缺字段给安全默认值，绝不抛异常。"""
    sections = _split_headers(md_text or "")

    # 标题：首个 H1
    name = ""
    for level, title, _ in sections:
        if level == 1:
            name = title
            # 去掉标题里的副标题段，如 "DADA2 - ASV 推断与降噪模块" 保留全名也行
            break
    if not name and sections:
        name = sections[0][1]

    # 基本信息
    info = {}
    info_body = _find_section(sections, "基本信息", "basic")
    if info_body:
        info = _kv_table(_parse_table(info_body))
    tool_name = (info.get("tool name") or "").strip() or ""
    description = (info.get("description") or info.get("描述") or "").strip()
    runtime = _parse_runtime(info.get("估算机时") or info.get("机时") or info.get("runtime") or "")
    cost = _parse_cost(info.get("报价分数") or info.get("报价") or info.get("cost") or "")

    # 输入 / 输出
    inputs: list[str] = []
    in_body = _find_section(sections, "输入")
    if in_body:
        for row in _parse_table(in_body):
            if row:
                fn = _clean_filename(row[0])
                if fn:
                    inputs.append(fn)

    outputs: list[str] = []
    out_body = _find_section(sections, "输出")
    if out_body:
        for row in _parse_table(out_body):
            if row:
                fn = _clean_filename(row[0])
                if fn:
                    outputs.append(fn)

    # 参数说明（可能是 ## 或 ###）
    param_body = _find_section(sections, "参数说明", "参数")
    call_params = _parse_params(_parse_table(param_body)) if param_body else []

    # call_outputs：由 outputs 派生（data_type 用文件名本身，保证和 inputs 匹配建图）
    call_outputs = [{"data_type": fn, "filename": fn} for fn in outputs]

    return {
        "name": name,
        "tool_name": tool_name,
        "description": description,
        "runtime": runtime,
        "cost": cost,
        "inputs": inputs,
        "outputs": outputs,
        "call_params": call_params,
        "call_outputs": call_outputs,
    }
