"""
脚本库画像生成器

文件夹导入一个库后，根据库内每个脚本的 .md 解析出的元信息
（name / description / category），用 LLM 生成这个库整体是干什么的描述与
关键词，供领域分流器（DomainClassifier）分类。

设计要点（核心是控制喂给 LLM 的上下文长度）：
- 绝不把 .md 全文喂 LLM；只喂「名称 + 分类 + 描述片段」的紧凑清单。
- 脚本数过多（> CAP）时按分类聚合（category rollup）：每类只给数量 + 代表名 +
  合并描述片段，行数从 N 收敛到「分类数」。
- LLM 失败（未配 key / 超时 / 返回非法 JSON）走确定性回退，导入流程永不因此失败。
- 一次 LLM 调用顺带产 example_queries（T4 few-shot 用）。本模块返回该字段，
  T1 写回阶段只用 description/keywords，待 T4 新增 domains.examples 字段后落盘。

输入 metas：list[{"name","description","category","tool_id"}]，由
ScriptService.upload_library 从 parse_md 结果 + 配对分类聚合而来。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

import httpx

from config.llm import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL_NAME,
    LLM_PARSER_TIMEOUT,
)

logger = logging.getLogger(__name__)

# 单库脚本数超过此值时按分类聚合，而非逐条列举
CAP = 80
# rollup 时每个分类展示的代表脚本名数量
REPS_PER_CATEGORY = 5
# 每条脚本描述喂给 LLM 的截断长度
DESC_TRUNC = 120


def summarize_library(metas: list[dict], domain_name: str) -> dict:
    """返回 {"description": str, "keywords": str, "example_queries": list[str]}。

    LLM 优先；任意失败走确定性回退。永不抛异常。
    """
    if not metas:
        return {"description": "", "keywords": "", "example_queries": []}

    entries_text = _build_entries(metas)
    llm_out = _summarize_llm(domain_name, entries_text)
    if llm_out is not None:
        return llm_out
    return _deterministic_summary(metas, domain_name)


def _build_entries(metas: list[dict]) -> str:
    """构造紧凑清单。脚本数 > CAP 时按分类聚合。"""
    valid = [m for m in metas if m.get("name")]
    if not valid:
        return ""
    if len(valid) > CAP:
        return _rollup_by_category(valid)
    lines = [
        f"- {m['name']}（分类:{m.get('category') or '未分类'}）："
        f"{(m.get('description') or '').strip()[:DESC_TRUNC]}"
        for m in valid
    ]
    return "\n".join(lines)


def _rollup_by_category(metas: list[dict]) -> str:
    """大库兜底：按分类聚合，每类 = 数量 + 代表名 + 合并描述片段。"""
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for m in metas:
        cat = m.get("category") or "未分类"
        if cat not in groups:
            groups[cat] = []
            order.append(cat)
        groups[cat].append(m)
    lines = [f"共 {len(metas)} 个脚本，按分类聚合："]
    for cat in order:
        items = groups[cat]
        names = [it["name"] for it in items if it.get("name")]
        reps = names[:REPS_PER_CATEGORY]
        descs = [
            d for d in ((it.get("description") or "").strip()[:60] for it in items) if d
        ]
        seg = "；".join(descs[:REPS_PER_CATEGORY])
        line = f"- 【{cat}】{len(items)} 个，代表：{'、'.join(reps)}"
        if seg:
            line += f"；流程：{seg}"
        lines.append(line)
    return "\n".join(lines)


def _summarize_llm(domain_name: str, entries_text: str) -> Optional[dict]:
    """一次 LLM 调用生成画像。失败返回 None（由调用方回退）。"""
    if not DASHSCOPE_API_KEY or not entries_text.strip():
        return None

    system = (
        "你是生物信息脚本库的画像生成器。下面给出一个分析脚本库里全部脚本的清单"
        "（名称、分类、描述）。据此输出一个 JSON 对象，描述这个库整体能做什么：\n"
        "- description：1-2 句概括这个库整体做什么——属于哪个生信领域、覆盖哪些分析"
        "类型、典型流程；面向「用户描述任务时能据此判断该归入哪个库」。\n"
        "- keywords：约 10 个逗号分隔的术语，必须是用户描述任务时真正会用的词，"
        "中文为主，可含 16S/ASV/RNA-seq 等缩写。\n"
        "- example_queries：2 条「用户会怎么向这个库提问」的真实问法（用于后续分流示例）。\n"
        "只输出 JSON，不要 markdown 代码块或解释。"
    )
    user = f"库名：{domain_name or '（未命名）'}\n脚本清单：\n{entries_text}"
    try:
        resp = httpx.post(
            f"{DASHSCOPE_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
            json={
                "model": DASHSCOPE_MODEL_NAME,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=LLM_PARSER_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(raw)
    except Exception as e:
        logger.warning(f"[library_summary] LLM 生成画像失败，走确定性回退：{e}")
        return None

    description = (data.get("description") or "").strip()
    keywords = _normalize_keywords(data.get("keywords"))
    examples = _coerce_examples(data.get("example_queries"))

    if not description:
        logger.warning(f"[library_summary] LLM 返回缺少 description，走回退：{raw[:200]}")
        return None
    logger.info(
        f"[library_summary] LLM 画像生成成功（desc {len(description)} 字，"
        f"kw {len(keywords)} 字，examples {len(examples)} 条）"
    )
    return {
        "description": description,
        "keywords": keywords,
        "example_queries": examples,
    }


def _normalize_keywords(raw) -> str:
    """把 LLM 返回的关键词整理成去重、逗号分隔的字符串。"""
    if isinstance(raw, list):
        kws = [str(k).strip() for k in raw if str(k).strip()]
    else:
        kws = [
            k.strip()
            for k in str(raw or "")
            .replace("，", ",")
            .replace("、", ",")
            .replace("；", ",")
            .split(",")
            if k.strip()
        ]
    seen = set()
    out = []
    for k in kws:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return ",".join(out[:12])


def _coerce_examples(raw) -> list[str]:
    """example_queries 可能是 list 或逗号串，统一成 list[str]，最多 2 条。"""
    if isinstance(raw, list):
        items = [str(e).strip() for e in raw if str(e).strip()]
    else:
        items = [
            e.strip()
            for e in str(raw or "").replace("，", ",").split(",")
            if e.strip()
        ]
    return items[:2]


def _deterministic_summary(metas: list[dict], domain_name: str) -> dict:
    """无 LLM / LLM 失败时的兜底：从分类与脚本名机械拼接。"""
    cats: list[str] = []
    for c in (m.get("category") or "" for m in metas):
        if c and c not in cats:
            cats.append(c)
    names = [m["name"] for m in metas[:10] if m.get("name")]
    if cats:
        description = f"本库包含 {len(metas)} 个脚本，覆盖：{'、'.join(cats)}。"
    else:
        description = f"本库包含 {len(metas)} 个分析脚本。"
    keywords = ",".join(_slug_of(n) for n in names if _slug_of(n))
    logger.info(f"[library_summary] 走确定性回退（desc {len(description)} 字）")
    return {"description": description, "keywords": keywords, "example_queries": []}


def _slug_of(name: str) -> str:
    """从脚本显示名抽一个关键词 token（取首个分隔符前的部分，去空白）。"""
    if not name:
        return ""
    token = re.split(r"[\s._\-/\\（(【\[\]]", name, maxsplit=1)[0]
    return token.strip()
