"""
独立单步分析理解代理（StandaloneAnalysisAgent）

Path B 的"大脑"：对一个已判定为【单步独立分析】的需求（生存分析/火山图/热图/…），
一次 LLM 推理，从通用生信常识判断：
- 信息够（sufficient=true）→ 给出精确的数据清单（data_requirements：文件/列名/格式）
  + 合理默认参数（params）+ 运行时提示（runtime_hint）。
- 信息不够（sufficient=false）→ questions[]：一次问全所有"不定就跑偏"的关键问题，
  像生信专家对待小白那样耐心但有效（见 STANDALONE_ANALYSIS_PLAN.md §0 诉求①、§4.2）。

与 IntentAgent（typed 多步）的区别：本代理**不依赖任何类型词表/typed 领域**，靠通用
生信常识直接产出"文件进→文件出"的清单，columns/format 必须精确（这是客户清单的核心价值）。
失败兜底：sufficient=false + 两个通用开放问题（数据/目标），不崩、不伪造。
"""

from __future__ import annotations

import json
import logging

import httpx

from config.llm import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL_NAME,
    LLM_UNDERSTAND_TIMEOUT,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
你是生物信息分析平台的【独立分析理解代理】，角色是**耐心的生信专家**。用户想做的是一个\
**单步独立分析**（一个自包含 R/python 脚本即可完成：文件进→文件出，无需多工具串联；\
例如生存分析、火山图、表达热图、组间差异比较、Lasso 回归、ROC、相关性分析、富集分析等）。

你的核心任务：**给用户一份"照着准备就能跑"的数据清单**——要哪些文件、每个文件需包含哪些列、\
什么格式、合理的默认参数。像专家对待小白：直接告诉他该准备什么，而不是审问他。

【判定哲学——默认 sufficient=true】
只要能看出用户想做【哪一种分析】，就 sufficient=true 并产出清单。把"用户没明说"的细节\
**用约定俗成的标准值兜住**，写进 data_requirements.columns / params.default，让用户在清单里\
看到、按需调整——**而不是用 questions 拦住他**。
- **列名：给出该分析约定俗成的标准列名**，让用户据此整理/重命名表头。例如：
  · 生存分析 → time 或 OS_time（总生存月数）+ status 或 OS_status（0存活/1死亡）；
  · 表达矩阵 → 行=基因、列=样本（给 gene_id + 样本列示例）；
  · 差异表/火山图 → log2FoldChange + pvalue（+ padj）；
  · 组间比较 → value（数值）+ group（分组）。
  **不要追问"你的列叫什么名字"**——直接给标准名，用户会照着改。
- **可调参数一律放 params 带 default + options**：如「结局指标 default=OS options=[OS,PFS,DSS]」\
「分组方法 default=中位数 options=[中位数,最优截断值,自定义]」「p值阈值 default=0.05」\
「log2FC 阈值 default=1.0」。

【何时才 sufficient=false】（少用）
仅当**分析目标本身完全不明**（如"帮我看看这数据""做个分析"看不出要干嘛），或存在\
**无法合理默认、且会改变整个分析性质**的根本性二选一（极少）。此时把关键问题一次问全\
（大白话、不挤牙膏、不出现内部代号）。data_requirements 仍可给能确定的骨架。

严格输出 JSON（不要 markdown 代码块、不要解释）：
{
  "sufficient": true | false,
  "questions": ["...", "..."],
  "analysis_type": "<规范中文名，如 Kaplan-Meier 生存分析>",
  "data_requirements": [
    {
      "key": "<英文小写短标识，如 clinical>",
      "label": "<中文标签，如 临床数据>",
      "required": true | false,
      "format": "<TSV|CSV|...>",
      "columns": ["<标准列名>", "..."],
      "columns_desc": "<列含义大白话，如 OS_time=总生存月数, OS_status=0存活/1死亡>",
      "multiple": false
    }
  ],
  "params": [
    {"key": "<英文短标识>", "label": "<中文标签>", "default": "<默认值>", "options": ["<可选值>", "..."]}
  ],
  "runtime_hint": "<R / python + 关键包，如 R / survival + survminer>",
  "reasoning": "<简短中文理由>"
}

字段规则：
- sufficient=true：data_requirements 列全所有"必需 + 常见可选"输入（别挤牙膏），columns/format\
  精确（给标准列名），params 给合理默认 + 可选项，questions 留空 []。
- sufficient=false：questions 一次问全；data_requirements/params 给能确定的骨架。
- questions 用中文大白话，**绝对不出现内部代号**（type_id、key 等）。
- multiple：该输入是否一次传多个文件（一般 false；仅批量样本/多文件合并时 true）。
- analysis_type 用规范中文名；runtime_hint 指明语言与关键包（真实可跑，不编造不存在的包）。
- 不要重复追问用户已在发言中明确给出的信息。
"""


# 兜底（LLM 不可用 / 失败）：只问"数据/目标"两个开放问题，绝不臆造列名。
_FALLBACK_QUESTIONS = [
    "你目前有什么数据？（例如：临床随访表、基因表达矩阵、差异基因列表等，最好说明文件格式和关键列）",
    "你想得到什么样的结果？（例如：KM 生存曲线、火山图、热图、两组差异比较等）",
]


def _fallback(reason: str) -> dict:
    return {
        "sufficient": False,
        "questions": list(_FALLBACK_QUESTIONS),
        "analysis_type": "",
        "data_requirements": [],
        "params": [],
        "runtime_hint": "",
        "reasoning": reason,
        "fallback": True,
    }


class StandaloneAnalysisAgent:
    """独立单步分析理解代理：一次常识推理输出清单/追问。"""

    @staticmethod
    def understand(content: str, history_dicts: list[dict] | None = None) -> dict:
        """返回 {sufficient, questions, analysis_type, data_requirements, params,
        runtime_hint, reasoning, fallback}。"""
        if not DASHSCOPE_API_KEY or not (content or "").strip():
            return _fallback("理解代理未配置或输入为空")

        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history_dicts:
            for msg in history_dicts[-20:]:
                if msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg.get("content", "")})

        messages.append({"role": "user", "content": f"【用户发言】\n{content}\n\n请判断并输出 JSON。"})

        try:
            resp = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": messages,
                },
                timeout=LLM_UNDERSTAND_TIMEOUT,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)
        except Exception as e:
            logger.warning(f"[StandaloneAgent] LLM 调用失败，走兜底: {type(e).__name__}: {e}")
            return _fallback("理解代理 LLM 调用失败")

        return StandaloneAnalysisAgent._normalize(data)

    @staticmethod
    def _normalize(data: dict) -> dict:
        sufficient = bool(data.get("sufficient", False))
        analysis_type = str(data.get("analysis_type") or "").strip()
        runtime_hint = str(data.get("runtime_hint") or "").strip()
        reasoning = str(data.get("reasoning") or "").strip()

        questions = [str(q).strip() for q in (data.get("questions") or []) if str(q).strip()]

        data_requirements = []
        for d in (data.get("data_requirements") or []):
            if not isinstance(d, dict):
                continue
            label = str(d.get("label") or "").strip()
            if not label:
                continue
            cols = [str(c).strip() for c in (d.get("columns") or []) if str(c).strip()]
            data_requirements.append({
                "key": str(d.get("key") or "").strip() or label,
                "label": label,
                "required": bool(d.get("required", False)),
                "format": str(d.get("format") or "").strip(),
                "columns": cols,
                "columns_desc": str(d.get("columns_desc") or "").strip(),
                "multiple": bool(d.get("multiple", False)),
            })

        params = []
        for p in (data.get("params") or []):
            if not isinstance(p, dict):
                continue
            label = str(p.get("label") or "").strip()
            if not label:
                continue
            opts = [str(o).strip() for o in (p.get("options") or []) if str(o).strip()]
            params.append({
                "key": str(p.get("key") or "").strip() or label,
                "label": label,
                "default": str(p.get("default") or "").strip(),
                "options": opts,
            })

        # 够意图但数据清单为空 → 降级追问，避免空清单
        if sufficient and not data_requirements:
            logger.info("[StandaloneAgent] sufficient 但 data_requirements 为空，降级追问")
            sufficient = False
            if not questions:
                questions = list(_FALLBACK_QUESTIONS)

        logger.info(
            f"[StandaloneAgent] sufficient={sufficient} analysis_type={analysis_type!r} "
            f"data_req={len(data_requirements)} params={len(params)} questions={len(questions)}"
        )
        return {
            "sufficient": sufficient,
            "questions": questions,
            "analysis_type": analysis_type,
            "data_requirements": data_requirements,
            "params": params,
            "runtime_hint": runtime_hint,
            "reasoning": reasoning,
            "fallback": False,
        }
