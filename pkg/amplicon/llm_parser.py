"""
LLM 驱动的自然语言解析器

使用 DashScope API (httpx) 将用户描述解析为结构化的
{available_inputs, goal_types, scenario_description, confidence}。
"""

from __future__ import annotations

import json
import logging

import httpx

from config.llm import DASHSCOPE_API_BASE, DASHSCOPE_API_KEY, DASHSCOPE_MODEL_NAME, LLM_PARSER_TIMEOUT
from pkg.amplicon.amplicon_tools import DATA_TYPE_NAMES

logger = logging.getLogger(__name__)


class LLMParserError(Exception):
    pass


class LLMNotConfiguredError(LLMParserError):
    pass


class LLMConnectionError(LLMParserError):
    pass


class LLMResponseError(LLMParserError):
    pass


SYSTEM_PROMPT = """\
你是一个生物信息学分析平台的自然语言理解模块。你的任务是从用户的描述中识别：
1. 用户拥有什么数据（available_inputs）
2. 用户想要什么分析结果（goal_types）

## ⚠️ 重要：输入有效性判断

首先判断用户输入是否与生物信息分析相关：
- 如果输入与生物信息分析完全无关（如问候语、无意义字符、"这是什么"、"start"等），必须返回空的 goal_types
- 如果输入太短且无明确分析意图（少于5个字符且无生物学术语），返回空的 goal_types
- 如果输入含义模糊但可能与分析相关，谨慎选择 goal_types，并设置 confidence 为 "low"

## 可用数据类型

以下是平台支持的所有数据类型ID及其含义。你必须严格从这些ID中选择，不能创造新的ID。

### 输入数据类型（用户可能已拥有的数据）：
- FASTQ_PAIR：双端测序原始数据（如Illumina下机的R1/R2 fastq文件）
- FASTA_SEQ：FASTA序列文件
- FASTQ_TRIMMED：引物切除后序列
- FASTQ_MERGED：FLASH拼接序列
- FASTQ_QC：质控后序列
- FEATURE_SEQS：ASV代表序列(QZA)
- FEATURE_TABLE：ASV丰度表(BIOM)
- FEATURE_FASTA：ASV序列(FASTA)
- ASV_TABLE：ASV特征表(含分类)
- ASV_TABLE_EVEN：均一化ASV表
- RELATIVE_ABUNDANCE：相对丰度表
- ROOTED_TREE：有根系统发育树(QZA)
- TREE_NWK：Newick格式树文件
- GROUP_EVEN_TABLE：组水平均一化表
- GROUP_REL_ABUNDANCE：组水平相对丰度
- EVEN_ABS_ABUNDANCE：均一化绝对丰度

### 分析目标数据类型（用户可能想获得的结果）：

#### 核心分析
- TAXONOMY_ASSIGN：物种分类注释结果

#### 多样性分析
- ALPHA_INDEX：Alpha多样性指数
- ALPHA_SIG：Alpha多样性检验结果
- DIST_MATRIX：Beta距离矩阵
- BETA_SIG：Beta多样性检验结果
- RAREFACTION_CURVE：稀疏曲线
- PCOA_COORDS：PCoA坐标
- UPGMA_TREE：UPGMA聚类树

#### 统计检验
- CATECOMP_RESULT：群落差异检验结果
- LEFSE_RESULT：LEfSe差异分析结果
- METASTAT_RESULT：MetaStat差异分析结果
- RF_RESULT：随机森林分类结果
- SIMPER_RESULT：SIMPER分析结果
- TTEST_RESULT：T检验/Wilcoxon结果

#### 可视化
- TOP_SPECIES：Top10物种柱状图
- GENUS_TREE：属水平系统发育树
- KRONA_CHART：Krona分类组成图
- NETWORK_2D：2D共发生网络图
- NETWORK_3D：3D网络图
- OTU_TREE：OTU系统发育树热图
- TAXA_HEATMAP：物种组成热图
- TAXA_GROUP_HEATMAP：分组物种热图
- TERNARY_CHART：三元相图
- VENN_CHART：Venn图

#### 排序分析
- PCA_PLOT：PCA排序图
- PCOA_PLOT：PCoA排序图
- NMDS_PLOT：NMDS非度量多维标度
- DCA_PLOT：DCA去趋势对应分析

#### 功能预测
- FUNC_PREDICTION：功能预测结果

## 识别规则

1. **available_inputs**：
   - 只有当用户明确说明或暗示有什么数据时才选择
   - 如果用户说"已有ASV表"/"已做完DADA2"/"去噪后"，选择 ["FEATURE_SEQS", "FEATURE_TABLE", "FEATURE_FASTA"]
   - 如果用户说"已做完质控"/"QC后"，选择 ["FASTQ_QC"]
   - 如果用户说"已拼接"，选择 ["FASTQ_MERGED"]
   - 如果用户说"已切除引物"，选择 ["FASTQ_TRIMMED"]
   - 如果用户没有说明有什么数据，返回空列表 []，不要猜测

2. **goal_types**：根据用户需求选择所有匹配的目标类型ID
   - 如果用户说"全流程"/"完整分析"/"全套"，选择物种注释+多样性+可视化的组合
   - 如果用户说"差异分析"但没指定方法，选择 ["LEFSE_RESULT", "TTEST_RESULT", "METASTAT_RESULT"]
   - 如果用户说"多样性"但没区分alpha/beta，同时选择 ["ALPHA_INDEX", "DIST_MATRIX"]
   - 如果用户说"排序"或"降维"但没指定方法，选择 ["PCA_PLOT", "PCOA_PLOT", "NMDS_PLOT"]
   - 如果无法确定用户想要什么分析，返回空列表 []

3. **confidence**：评估把握程度
   - "high"：用户描述清晰，明确说明了数据类型和分析目标
   - "medium"：用户有一定意图，但部分信息需要推测
   - "low"：用户输入模糊，与生物信息分析关联性弱，或包含过多无关内容

4. **scenario_description**：用一句话总结，格式如"从{输入数据}出发，目标：{分析目标}"

## 输出格式

严格输出JSON，不要输出任何其他内容：
{
  "available_inputs": ["DATA_TYPE_ID", ...],
  "goal_types": ["DATA_TYPE_ID", ...],
  "scenario_description": "...",
  "confidence": "high" | "medium" | "low"
}

记住：当输入与生物信息分析无关时，goal_types 必须为空数组 []，不要试图猜测用户的意图。
"""

CLARIFICATION_SYSTEM_PROMPT = """\
你是一个生物信息学分析平台的智能助手。用户想要进行生物信息分析，但是他们的描述不够清晰，
无法确定他们拥有什么数据或者想要什么分析结果。

你的任务是：
1. 友好地回应用户的输入
2. 分析用户可能想要做什么
3. 引导用户说明以下信息：
   - 他们拥有什么类型的数据（如：原始测序数据 FASTQ、ASV 表、物种注释结果等）
   - 他们想要获得什么样的分析结果（如：物种组成、多样性分析、差异分析、可视化图表等）

## 平台支持的分析类型

### 数据处理流程
- 原始数据质控（QC）
- 引物切除、序列拼接
- DADA2 去噪生成 ASV
- 物种分类注释

### 多样性分析
- Alpha 多样性（Shannon、Simpson、Chao1 等指数）
- Beta 多样性（PCoA、NMDS、UPGMA 聚类等）
- 稀疏曲线

### 差异分析
- LEfSe 线性判别分析
- MetaStat 差异检验
- T 检验 / Wilcoxon 检验
- 群落组成比较（CATECOMP）

### 可视化
- 物种组成柱状图、热图
- Krona 交互图
- 系统发育树
- 共发生网络图（2D/3D）
- Venn 图、三元相图

### 功能预测
- PICRUSt2 功能预测

请用简洁、友好的语气回复，不要超过 200 字。
"""


def _call_llm(messages: list[dict], temperature: float = 0.1, json_mode: bool = True) -> str:
    """Call DashScope API using httpx (matches AIService pattern)."""
    payload = {
        "model": DASHSCOPE_MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    # Log input (truncate long content for readability)
    log_messages = []
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str) and len(content) > 200:
            content = content[:200] + f"...({len(content)} chars)"
        elif isinstance(content, list):
            parts = []
            for part in content:
                if part.get("type") == "text":
                    t = part.get("text", "")
                    parts.append(f"[text] {t[:200]}{'...' if len(t) > 200 else ''}")
                elif part.get("type") == "image_url":
                    parts.append("[image_url]")
            content = parts
        log_messages.append({"role": m["role"], "content": content})
    logger.info(f"[LLM] 请求模型={DASHSCOPE_MODEL_NAME}, temperature={temperature}, json_mode={json_mode}")
    logger.info(f"[LLM] 输入消息: {json.dumps(log_messages, ensure_ascii=False)}")

    response = httpx.post(
        f"{DASHSCOPE_API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
        json=payload,
        timeout=LLM_PARSER_TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    raw = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    logger.info(f"[LLM] 输出(usage: prompt={usage.get('prompt_tokens','?')}, completion={usage.get('completion_tokens','?')}): {raw[:500]}{'...' if len(raw) > 500 else ''}")
    return raw


def parse_natural_language(user_input: str, conversation_history: list[dict] | None = None) -> dict:
    """
    使用 LLM 解析用户自然语言描述。
    返回: {available_inputs, goal_types, scenario_description, confidence}
    """
    logger.info(f"[LLM Parser] 收到用户输入: {user_input}")

    if not DASHSCOPE_API_KEY:
        raise LLMNotConfiguredError("LLM 服务未配置，请检查 DASHSCOPE_API_KEY 环境变量")

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if conversation_history:
            recent = conversation_history[-20:]
            for msg in recent:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg.get("content", ""),
                    })

        messages.append({"role": "user", "content": user_input})

        raw = _call_llm(messages, temperature=0.1, json_mode=True)
        logger.info(f"[LLM Parser] LLM 原始响应: {raw}")

        parsed = json.loads(raw)
        result = {
            "available_inputs": parsed.get("available_inputs", []),
            "goal_types": parsed.get("goal_types", []),
            "scenario_description": parsed.get("scenario_description", ""),
            "confidence": parsed.get("confidence", "medium"),
        }

        if _validate(result):
            return result

        raise LLMResponseError("LLM 返回的数据格式不正确，请重试")

    except LLMParserError:
        raise
    except Exception as e:
        logger.error(f"[LLM Parser] LLM 调用异常: {type(e).__name__}: {e}")
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            raise LLMConnectionError(f"连接 LLM 服务失败: {e}")
        raise LLMResponseError(f"LLM 解析失败: {e}")


def generate_clarification_prompt(user_input: str, conversation_history: list[dict] | None = None) -> str:
    """当无法解析出有效信息时，调用 LLM 生成友好的澄清提示。"""
    if not DASHSCOPE_API_KEY:
        raise LLMNotConfiguredError("LLM 服务未配置")

    try:
        messages = [{"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT}]

        if conversation_history:
            recent = conversation_history[-10:]
            for msg in recent:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg.get("content", ""),
                    })

        messages.append({"role": "user", "content": user_input})
        return _call_llm(messages, temperature=0.7, json_mode=False)

    except Exception as e:
        logger.error(f"[LLM Parser] 生成澄清提示失败: {type(e).__name__}: {e}")
        return (
            "为了更好地为您规划分析流程，请告诉我：\n"
            "1. 您目前拥有什么类型的数据？（如原始测序数据、ASV 表等）\n"
            "2. 您希望获得什么样的分析结果？（如物种组成、多样性分析、差异分析等）"
        )


def _validate(result: dict) -> bool:
    valid_ids = set(DATA_TYPE_NAMES.keys())
    inputs = result.get("available_inputs")
    goals = result.get("goal_types")

    if not isinstance(inputs, list):
        return False
    if not isinstance(goals, list):
        return False

    if goals:
        invalid = [g for g in goals if g not in valid_ids]
        if invalid:
            logger.error(f"[LLM Parser] 无效 goal IDs: {invalid}")
            return False

    if inputs:
        invalid = [i for i in inputs if i not in valid_ids]
        if invalid:
            logger.error(f"[LLM Parser] 无效 input IDs: {invalid}")
            return False

    return True
