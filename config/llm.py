import os

# DashScope (AliBailian) API configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_API_BASE = os.getenv(
    "DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
DASHSCOPE_MODEL_NAME = os.getenv("DASHSCOPE_MODEL_NAME", "qwen-plus")
LLM_PARSER_TIMEOUT = int(os.getenv("LLM_PARSER_TIMEOUT", "30"))
LLM_CODEGEN_TIMEOUT = int(os.getenv("LLM_CODEGEN_TIMEOUT", "120"))
# 独立分析理解/形态判定等较重的常识推理调用（prompt 长、输出 JSON 大），30s 偶发超时
LLM_UNDERSTAND_TIMEOUT = int(os.getenv("LLM_UNDERSTAND_TIMEOUT", "60"))
