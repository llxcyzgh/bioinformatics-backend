"""轻量表格画像：csv/tsv/txt → 列名/行数/类型/缺失/前5行预览。

喂给 Agent，让它用对真实列名/格式——这正是"上传后生成"相对"盲生成"的核心价值
（P0 实测：先 Read 看清数据 → 一次写对，attempts 1/5）。

零依赖（仅标准库 csv），便于在任何环境单测。xlsx 等二进制格式留后续（需 pandas/openpyxl）。
"""
from __future__ import annotations

import csv
from pathlib import Path


def _infer_type(vals: list[str]) -> str:
    """对一列样本推断 number/string。>80% 可解析为数值 → number。"""
    nums = 0
    nonempty = 0
    for v in vals[:200]:
        if v is None or v == "":
            continue
        nonempty += 1
        try:
            float(v)
            nums += 1
        except (ValueError, TypeError):
            pass
    if nonempty == 0:
        return "empty"
    return "number" if nums / nonempty > 0.8 else "string"


def profile_table(path, max_rows_preview: int = 5, max_cols: int = 50) -> dict:
    """单个表格文件画像。返回 {file, format, rows, columns:[{name,type}], preview, delimiter} 或 {file, error}。"""
    p = Path(path)
    if not p.exists():
        return {"file": p.name, "error": "文件不存在"}
    ext = p.suffix.lower()
    delim = "\t" if ext in (".tsv", ".txt") else ","
    try:
        with open(p, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f, delimiter=delim))
    except Exception as e:
        return {"file": p.name, "error": f"读取失败: {type(e).__name__}: {e}"}
    if not rows:
        return {"file": p.name, "format": ext.lstrip("."), "rows": 0, "columns": [], "preview": []}
    header = rows[0]
    data = rows[1:]
    columns = []
    for i, name in enumerate(header[:max_cols]):
        col_vals = [r[i] for r in data if i < len(r)]
        columns.append({"name": (name or f"col{i+1}").strip(), "type": _infer_type(col_vals)})
    return {
        "file": p.name,
        "format": ext.lstrip(".") or "csv",
        "rows": len(data),
        "delimiter": delim,
        "columns": columns,
        "preview": data[:max_rows_preview],
    }


def profile_files(input_dir) -> list[dict]:
    """对目录下所有 csv/tsv/txt 文件画像，返回列表（按文件名排序）。"""
    out = []
    for p in sorted(Path(input_dir).glob("*")):
        if p.is_file() and p.suffix.lower() in (".csv", ".tsv", ".txt"):
            out.append(profile_table(p))
    return out
