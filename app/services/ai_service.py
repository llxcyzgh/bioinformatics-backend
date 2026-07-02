import json
from typing import List

import httpx

from app.models import Message
from config import DASHSCOPE_API_BASE, DASHSCOPE_API_KEY, DASHSCOPE_MODEL_NAME, LLM_PARSER_TIMEOUT

SYSTEM_PROMPT = """你是一个专业的生物信息学 AI 助手。你的任务是与用户进行交互式对话，帮助用户完成生物信息学分析工作。

根据对话上下文，你需要判断当前应该返回哪种类型的响应：

1. **text** - 当用户提出一般性问题、需要解释或建议时，返回纯文本回答。
2. **path** - 当用户需要选择分析路径或方案时，返回可供选择的选项列表。
3. **code** - 当用户已经选择了某个路径，需要你生成具体的分析代码时，返回代码及相关元数据。
4. **file_request** - 当你需要用户提供特定文件才能继续分析时，返回文件要求。

你必须返回严格的 JSON 格式，不要包含 markdown 代码块标记或其他额外文本：

{
  "type": "text|path|code|file_request",
  "content": "主要文本内容（代码、说明或选项描述）",
  "data": "额外的结构化数据JSON字符串"
}

各类型的 data 字段要求：
- text: 空字符串 ""
- path: JSON数组，包含选项对象 [{"label": "选项1", "description": "描述"}, ...]
- code: JSON对象，包含 {"security_review": "安全审查结果", "required_files": ["文件1", "文件2"]}
- file_request: JSON数组，包含需要的文件列表 ["file1.fa", "file2.fastq"]
"""


class AIService:
    """AI service for generating system responses via AliBailian (DashScope) LLM."""

    @staticmethod
    def _build_messages(conversation_history: List[Message]) -> List[dict]:
        """Convert conversation history to OpenAI-compatible messages format."""
        messages: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in conversation_history:
            # Map internal role names to OpenAI roles
            # 'user' stays 'user', 'system' (AI) maps to 'assistant'
            role = msg.role if msg.role == "user" else "assistant"
            messages.append({"role": role, "content": msg.content})
        return messages

    @staticmethod
    def _call_llm(messages: List[dict]) -> dict:
        """Make HTTP call to DashScope compatible-mode API."""
        import logging
        logger = logging.getLogger(__name__)
        log_msgs = [{"role": m["role"], "content": (m.get("content", "")[:200] + "..." if isinstance(m.get("content"), str) and len(m.get("content", "")) > 200 else m.get("content"))} for m in messages]
        logger.info(f"[AIService] LLM请求(model={DASHSCOPE_MODEL_NAME}): {json.dumps(log_msgs, ensure_ascii=False)}")

        response = httpx.post(
            f"{DASHSCOPE_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"},
            json={
                "model": DASHSCOPE_MODEL_NAME,
                "messages": messages,
            },
            timeout=LLM_PARSER_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        ai_content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        logger.info(f"[AIService] LLM输出(usage: prompt={usage.get('prompt_tokens','?')}, completion={usage.get('completion_tokens','?')}): {ai_content[:500]}")
        return json.loads(ai_content)

    @staticmethod
    def _validate_response(response: dict) -> dict:
        """Validate LLM response has required keys and normalize defaults."""
        if not isinstance(response, dict):
            raise ValueError("LLM response is not a dict")

        required_keys = {"type", "content", "data"}
        if not required_keys.issubset(response.keys()):
            raise ValueError(f"LLM response missing required keys: {required_keys - response.keys()}")

        valid_types = {"text", "path", "code", "file_request"}
        if response["type"] not in valid_types:
            raise ValueError(f"Invalid type from LLM: {response['type']}")

        # data 列是 Text：必须落 JSON 字符串。LLM 对 path/code 类型会直接返回数组/对象，
        # 这里统一序列化，避免 list/dict 直接塞进 Message.data 触发 SQLite 绑定错误。
        data = response.get("data", "")
        if not isinstance(data, str):
            data = json.dumps(data, ensure_ascii=False) if data else ""

        return {
            "type": response["type"],
            "content": response.get("content", ""),
            "data": data,
        }

    @staticmethod
    def _placeholder_response(user_message: Message) -> dict:
        """Fallback placeholder when LLM is unavailable."""
        if user_message.type == "text":
            return {
                "type": "text",
                "content": f"AI response to: {user_message.content}",
                "data": "",
            }

        if user_message.type == "path":
            return {
                "type": "code",
                "content": "print('hello world')",
                "data": json.dumps({"security_review": "passed"}, ensure_ascii=False),
                "required_files": json.dumps(["sample.txt"], ensure_ascii=False),
            }

        return {
            "type": "text",
            "content": "...",
            "data": "",
        }

    @staticmethod
    def generate_response(
        task_id: int,
        user_message: Message,
        conversation_history: List[Message],
    ) -> dict:
        """Generate an AI system response.

        Attempts to call the real DashScope LLM. Falls back to placeholder
        if the API key is missing or any step fails.
        """
        if not DASHSCOPE_API_KEY:
            return AIService._placeholder_response(user_message)

        try:
            messages = AIService._build_messages(conversation_history)
            response = AIService._call_llm(messages)
            return AIService._validate_response(response)
        except Exception:
            # Any failure (network, timeout, parse error, validation) → fallback
            return AIService._placeholder_response(user_message)
