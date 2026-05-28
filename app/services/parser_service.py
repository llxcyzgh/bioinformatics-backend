"""
统一自然语言解析服务

LLM 优先，关键词回退，都失败返回空结果。
"""

import logging

from pkg.amplicon import llm_parser, nl_parser
from config.llm import DASHSCOPE_API_KEY

logger = logging.getLogger(__name__)


class ParserService:

    @staticmethod
    def parse(user_input: str, conversation_history: list[dict] | None = None) -> dict:
        """
        解析用户输入，返回:
        {available_inputs: list[str], goal_types: list[str],
         scenario_description: str, confidence: "high"|"medium"|"low"}
        """
        if DASHSCOPE_API_KEY:
            try:
                result = llm_parser.parse_natural_language(user_input, conversation_history)
                logger.info(f"[ParserService] LLM 解析成功: {result}")
                return result
            except Exception as e:
                logger.warning(f"[ParserService] LLM 解析失败，尝试关键词回退: {e}")

        try:
            result = nl_parser.parse_natural_language(user_input)
            logger.info(f"[ParserService] 关键词解析结果: {result}")
            return result
        except Exception as e:
            logger.error(f"[ParserService] 关键词解析失败: {e}")
            return {
                "available_inputs": [],
                "goal_types": [],
                "scenario_description": "",
                "confidence": "low",
            }

    @staticmethod
    def generate_clarification(user_input: str, conversation_history: list[dict] | None = None) -> str:
        """生成追问提示文本"""
        if DASHSCOPE_API_KEY:
            try:
                return llm_parser.generate_clarification_prompt(user_input, conversation_history)
            except Exception as e:
                logger.warning(f"[ParserService] 生成澄清提示失败: {e}")

        return (
            "为了更好地为您规划分析流程，请告诉我：\n"
            "1. 您目前拥有什么类型的数据？（如原始测序数据、ASV 表等）\n"
            "2. 您希望获得什么样的分析结果？（如物种组成、多样性分析、差异分析等）"
        )
