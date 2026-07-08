"""
形态判定器（AnalysisRouter）

在相关性闸之后、typed 意图理解之前，判断一个"合理生信任务"是
【单步独立分析】(standalone) 还是 【多步流水线】(pipeline)：

- standalone = 一个**自包含**脚本（R 或 python）即可解决（文件进→文件出），
  无需多工具串联。例：生存分析 / 火山图 / 热图(表达矩阵) / 组间比较 / Lasso 回归。
- pipeline   = 需要多个工具串成流水线。
  例：16S 原始 fastq → 质控 → 去噪(DADA2) → 物种注释 → 多样性 → PCoA。

这是 Path B（独立单步分析闭环）与老路（planner 多步）的分流点（见
STANDALONE_ANALYSIS_PLAN.md §1/§4.1）。

保守策略：拿不准 → pipeline（老路有 ToolGenesis 兜底，更安全；避免把多步任务
误判成单步、生成一个跑不通的"伪单脚本"）。

输出：{form: "standalone"|"pipeline", analysis_type: str, reasoning: str}
未配置 key / 失败 → form="pipeline"（保守，走老路）。
"""

from __future__ import annotations

import json
import logging

import httpx

from config.llm import (
    DASHSCOPE_API_BASE,
    DASHSCOPE_API_KEY,
    DASHSCOPE_MODEL_NAME,
    LLM_PARSER_TIMEOUT,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """\
你是生物信息分析平台的【任务形态判定器】。判断用户的分析需求属于哪种形态：

- **standalone（单步独立分析）**：一个**自包含**的脚本（R 或 python）就能解决——\
给它输入文件，它直接产出结果文件，无需把多个工具串成流水线。\
典型：生存分析(KM 曲线/Cox)、火山图、热图(表达矩阵)、组间差异比较\
(T 检验/Wilcoxon/DESeq2)、Lasso 回归、ROC 曲线、相关性分析、富集分析\
(已有表达矩阵/差异基因列表)等。
- **pipeline（多步流水线）**：需要从原始/中间数据经过**多个工具串联**才能到目标，\
或本质上是"一条分析流水线"。\
典型：16S 原始 fastq → 质控 → 去噪(DADA2) → 物种注释 → 多样性 → PCoA；\
宏基因组 raw reads → 拼接 → 基因预测 → 功能注释；RNA-seq raw reads → 比对 → 定量 → 差异。

判定要点：
- 看【是否需要多工具串联】：是 → pipeline；一个脚本进/出即可 → standalone。
- 用户已具备"算好的表/矩阵/列表"，只做单一下游可视化/统计 → standalone。
- 从原始测序数据出发、要做完整流水线 → pipeline。
- **拿不准时判 pipeline**（多步走老路有兜底，更安全）。

同时给出该任务的【分析类型】（规范中文名，如「Kaplan-Meier 生存分析」「基因表达火山图」）。

严格输出 JSON（不要 markdown 代码块、不要解释）：
{"form": "standalone" | "pipeline", "analysis_type": "<规范中文名>", "reasoning": "<简短中文理由>"}
"""


class AnalysisRouter:
    """形态判定器：standalone vs pipeline。一次廉价 LLM 调用。"""

    @staticmethod
    def classify_form(content: str, verdict: dict | None = None) -> dict:
        """返回 {form: "standalone"|"pipeline", analysis_type: str, reasoning: str}。

        - verdict：相关性闸结果（可选），仅用于把领域判语附加到 prompt 供参考。
        - 未配置 key / 输入为空 / LLM 失败 → 保守返回 pipeline（form fallback）。
        """
        if not DASHSCOPE_API_KEY or not (content or "").strip():
            return AnalysisRouter._fallback("未配置 key 或输入为空")

        domain_hint = ""
        if verdict:
            reason = (verdict.get("reason") or "").strip()
            if reason:
                domain_hint = f"【领域闸判语（参考）】{reason}\n\n"

        try:
            resp = httpx.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
                json={
                    "model": DASHSCOPE_MODEL_NAME,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"{domain_hint}【用户发言】\n{content}\n\n请判定任务形态。"},
                    ],
                },
                timeout=LLM_PARSER_TIMEOUT,
            )
            resp.raise_for_status()
            data = json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            logger.warning(f"[AnalysisRouter] 形态判定失败，保守判 pipeline: {type(e).__name__}: {e}")
            return AnalysisRouter._fallback("形态判定 LLM 调用失败")

        form = str(data.get("form") or "").strip().lower()
        analysis_type = str(data.get("analysis_type") or "").strip()
        reasoning = str(data.get("reasoning") or "").strip()

        if form not in ("standalone", "pipeline"):
            logger.warning(f"[AnalysisRouter] 未知 form={form!r}，保守判 pipeline")
            form = "pipeline"

        logger.info(f"[AnalysisRouter] form={form} analysis_type={analysis_type!r}")
        return {"form": form, "analysis_type": analysis_type, "reasoning": reasoning}

    @staticmethod
    def _fallback(reason: str) -> dict:
        """保守兜底：判 pipeline（走老路，有 ToolGenesis 兜底）。"""
        return {"form": "pipeline", "analysis_type": "", "reasoning": reason}
