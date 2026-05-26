import os

# DashScope (AliBailian) API configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_API_BASE = os.getenv(
    "DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
DASHSCOPE_MODEL_NAME = os.getenv("DASHSCOPE_MODEL_NAME", "qwen-plus")
LLM_PARSER_TIMEOUT = int(os.getenv("LLM_PARSER_TIMEOUT", "30"))
