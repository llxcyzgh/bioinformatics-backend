"""Path B 智能代码 Agent 配置。

SDK 路子：用 Claude Agent SDK（claude-agent-sdk）驱动 claude CLI 子进程，
自定义工具 run_validation / validate_delivery 以 **in-process** 工具形式挂载
（@tool + create_sdk_mcp_server），不起独立 MCP 进程。

模型走智谱 BigModel 的 Anthropic 兼容端点（glm-5.2）。后端进程（www）起 SDK 子进程时，
通过 options.env 注入凭证，**不复用 zjiaai 的 ~/.claude 登录态**——避免 www 跨用户读文件。
故后端 .env 必须配置 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_MODEL。
"""
import os

# ---- Agent 运行参数 ----
# Path B 总开关：开(1)=用 Agent 生成+验证+debug 闭环（连智谱 glm-5.2）；
# 关(0)=老路一次性盲生成（StandaloneScriptService._generate）。灰度用。
CODEAGENT_ENABLED = os.getenv("CODEAGENT_ENABLED", "0") == "1"
# run_validation 最大调用次数（硬限制，防空转/烧 token）
CODEAGENT_MAX_ATTEMPTS = int(os.getenv("CODEAGENT_MAX_ATTEMPTS", "5"))
# 单次沙箱执行超时（秒）
CODEAGENT_EXEC_TIMEOUT = int(os.getenv("CODEAGENT_EXEC_TIMEOUT", "120"))
# 单会话最大 turn 数（一个 turn = 一次 user+assistant）
CODEAGENT_MAX_TURNS = int(os.getenv("CODEAGENT_MAX_TURNS", "24"))
# 模型；空串 = 走 SDK 子进程读到的默认（settings.json 的 ANTHROPIC_MODEL）
CODEAGENT_MODEL = os.getenv("CODEAGENT_MODEL", "")

# ---- 任务工作区 ----
# 每个 standalone 任务一个独立目录：<JOBS_ROOT>/<task_id>/{input,code,output,logs,delivery}
# input 软链/复制真实上传文件（只读），code 放 analysis.sh，output 放验证产物
CODEAGENT_JOBS_ROOT = os.getenv("CODEAGENT_JOBS_ROOT", "storage/codeagent_jobs")

# ---- Sandbox 模式 ----
# local : 本机 bash 跑脚本（P0/P1 验证；非隔离，仅用于可信测试数据）
# docker: docker exec sge-master 跑（生产隔离；需后端用户有 docker 权限）
CODEAGENT_SANDBOX = os.getenv("CODEAGENT_SANDBOX", "local")
CODEAGENT_SANDBOX_CONTAINER = os.getenv("CODEAGENT_SANDBOX_CONTAINER", "sge-master")

# ---- 智谱/Anthropic 凭证（注入 SDK 子进程；从后端 .env 读）----
_BASE = os.getenv("ANTHROPIC_BASE_URL", "")
_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
_MODEL = os.getenv("ANTHROPIC_MODEL", "glm-5.2")
# SDK 子进程靠这几个 env 连智谱；只保留非空项
CODEAGENT_SDK_ENV = {
    k: v for k, v in {
        "ANTHROPIC_BASE_URL": _BASE,
        "ANTHROPIC_AUTH_TOKEN": _TOKEN,
        "ANTHROPIC_MODEL": _MODEL,
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    }.items() if v
}

# ---- 内置工具白名单（claude 会话只放开这几个内置工具）----
CODEAGENT_ALLOWED_TOOLS = ["Read", "Write", "Edit"]

# ---- in-process MCP server 命名空间（工具全限定名前缀 mcp__<server>__<tool>）----
CODEAGENT_MCP_SERVER = "bioflow"
