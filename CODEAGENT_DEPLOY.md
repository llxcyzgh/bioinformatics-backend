# BioFlow 智能代码 Agent（Path B）部署文档

> 本文档面向**从零部署**：在新服务器上拉取 BioFlow 后端代码，启用本次重大更改（用 Claude Agent SDK 替代 Path B 一次性盲生成），并完成验证测试。
>
> 本次改动分支：`feat/standalone-code-agent`（**不在 `main` 上**），基线 commit `f41b1b4`。

---

## 1. 本次重大更改概述

### 改了什么
Path B（独立单步分析，如差异表达、统计排序等单脚本类任务）的代码生成方式变更：

| | 旧（`CODEAGENT_ENABLED=0`） | 新（`CODEAGENT_ENABLED=1`） |
|---|---|---|
| 生成方式 | LLM 一次性盲生成脚本 | Claude Agent SDK 闭环：**生成 → bash 语法 / shellcheck 校验 → sandbox 试跑 → 自检 debug → 交付** |
| 交付物 | 未经验证的 R/python 脚本 | 经过试跑验证的 bash `analysis.sh`（合同：`INPUT_DIR` / `OUTPUT_DIR` + `result.json`）|
| 失败处理 | 无 | 自动 debug 重试（≤ `CODEAGENT_MAX_ATTEMPTS` 次）|

### 影响范围
- ✅ **仅影响 Path B**（standalone 单步分析）
- ❌ Path A（amplicon 多步 pipeline）**不受影响**
- 🔒 **灰度开关** `CODEAGENT_ENABLED`，默认 **关闭（0）** = 完全老行为，可随时回退（见 §6）

### 接入点
用户上传数据 → `confirm_upload` → 触发 Agent 编排（生成 + 验证闭环）→ 归档验证过的脚本 → `start_execution` 执行（现状仍为 simulation）。

---

## 2. 环境要求

| 项 | 要求 |
|---|---|
| Python | **≥ 3.10**（推荐 3.13；SDK 不支持 3.6 / 3.7）|
| 系统 | Linux + `bash` |
| `shellcheck` | **可选**（不装则跳过该校验、不报错；装了校验更严）|
| 网络 | 能访问智谱 BigModel API（默认）或 Anthropic API |
| SGE / Docker | **不强制**（验证用 local sandbox；真 SGE 执行为 deferred，见 §7）|

---

## 3. 从零部署

```bash
# 0. 拉代码（注意：本次改动在 feature 分支，不在 main）
git clone git@github.com:llxcyzgh/bioinformatics-backend.git
cd bioinformatics-backend
git checkout feat/standalone-code-agent      # ← 本次重大更改所在分支

# 1. 建 venv（用 3.10+ 的 python，此处以 3.13 为例）
python3.13 -m venv .venv
source .venv/bin/activate

# 2. 装后端依赖
pip install -r requirements.txt

# 3. 装本次新增依赖：Claude Agent SDK
#    （体积大、捆绑 CLI，未进 requirements.txt；单独装。PyPI 直连易超时，建议用镜像）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple claude-agent-sdk

# 4.（可选但推荐）装 shellcheck
#    Ubuntu/Debian: sudo apt install shellcheck
#    CentOS/RHEL:   sudo yum install shellcheck
#                  或见 https://github.com/koalaman/shellcheck

# 5. 配环境变量
cp .env.example .env
#   编辑 .env：填 JWT / DATABASE / DASHSCOPE，并把 CODEAGENT 段按 §4 填好

# 6. 初始化数据库（建表 + seed 用户/脚本）
python migrate_seed.py

# 7. 起服务（dev）
uvicorn main:app --host 0.0.0.0 --port 8000
#   生产：用 systemd / 宝塔 Python 项目 / supervisor 守护，host 127.0.0.1 + nginx 反代
```

启动后访问 `http://<host>:8000/docs` 应能看到 Swagger 文档。

---

## 4. 配置 CODEAGENT（.env）

`.env.example` 已含 CODEAGENT 段，按需填写：

```env
# 总开关：1=启用 Agent 闭环；0=老路（默认，本次改动不生效）
CODEAGENT_ENABLED=1

# ---- 智谱 BigModel（Anthropic 兼容端点）----
# 默认走智谱；也可改为 Anthropic 官方 https://api.anthropic.com
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
# 智谱 API token（开放平台申请；本机 ~/.claude/settings.json 的 env 块也有现成的）
ANTHROPIC_AUTH_TOKEN=<你的智谱 token>
ANTHROPIC_MODEL=glm-5.2

# ---- 可选调参（均有默认值，可不填）----
CODEAGENT_MAX_ATTEMPTS=5     # run_validation 最大调用次数（防空转烧 token）
CODEAGENT_EXEC_TIMEOUT=120   # 单次沙箱执行超时（秒）
CODEAGENT_MAX_TURNS=24       # 单会话最大 turn 数
CODEAGENT_SANDBOX=local      # local（本机 bash，非隔离）| docker（docker exec，需权限）
```

> **凭证来源**：智谱开放平台 https://open.bigmodel.cn 申请 API Key；或在已配置 Claude Code 的机器上读取 `~/.claude/settings.json` 的 `env` 块里的 `ANTHROPIC_AUTH_TOKEN`。

---

## 5. 验证测试

### 5.1 健康检查
- `GET /docs` 能打开 Swagger
- `POST /api/login` 用 seed 账号登录拿 token（`admin@bioflow.com` / `admin123`）

### 5.2 端到端（推荐用前端 UI）
最贴近真实、不依赖脆弱的 API 序列：部署前端后，正常走
**建任务 → 用自然语言描述一个单步分析需求（触发 Path B / standalone 路由）→ 系统给数据清单 → 上传数据 → 确认上传（confirm-upload）**

### 5.3 成功信号（怎么确认 Agent 真触发了）
确认上传后，观察以下任一信号：

1. **后端日志**出现 CODEAGENT 相关编排输出（Agent 编排、validation、attempts 记录）
2. **工作区目录**生成：`storage/codeagent_jobs/<task_id>/`，内含 `input/` `code/analysis.sh` `output/` `logs/` `delivery/`
3. **确认上传返回**的 `generated_code` 是一段 wrapper（含 `INPUT_DIR` / `OUTPUT_DIR=/.../task_<id>/{input,output}` 和 `bash -euo pipefail <<'__CODEAGENT_ANALYSIS_SH__'`），而不是老的裸 R/python 脚本
4. 归档记录存在（slug 形如 `agent-<task_id>`）

### 5.4 关键 API 端点（供纯后端测试 / Swagger 调用）

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/login` | 登录拿 token |
| POST | `/api/chat/` | 发消息（Form: `project_id`, `content`, `task_uuid`…）|
| POST | `/api/chat/confirm-path` | 确认分析路径 |
| POST | `/api/uploads/` | 上传文件（multipart: `file`, `task_id`）|
| POST | `/api/chat/confirm-upload` | **确认上传 → 触发 Agent**（JSON: `task_uuid`, `project_id`, `file_mappings[]`）|
| POST | `/api/chat/start-execution` | 执行（现状 simulation）|

---

## 6. 回退（零风险）
`.env` 设 `CODEAGENT_ENABLED=0` → 重启后端 → 立即回到老的一次性盲生成，本次改动完全不介入。

---

## 7. 已知限制 / 后续
- **local sandbox 非隔离**：验证时用本机 bash 跑生成的脚本，仅适合可信测试数据；生产隔离需切 `CODEAGENT_SANDBOX=docker`（待配置 docker 权限）。
- **SGE 真执行 deferred**：`start_execution` 现状跑 simulation（无真 qsub 环境），**不影响** Agent 生成 + 验证闭环本身的测试。
- **智谱 token 计费**：每次 Agent 闭环会调用智谱 API，注意额度。
- SDK 未进 `requirements.txt`（体积大 + 捆绑 CLI），按 §3.3 单独装。

---

## 8. 故障排查

| 现象 | 排查 |
|---|---|
| `ModuleNotFoundError: claude_agent_sdk` | SDK 没装进**运行后端的那个 python**（venv）；确认 §3.3 装对 |
| confirm-upload 报智谱 401 / 403 | 检查 `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_BASE_URL` |
| Agent 跑很久 / 超时 | 调大 `CODEAGENT_EXEC_TIMEOUT` / `CODEAGENT_MAX_TURNS`；复杂任务 attempts 多 |
| 生成脚本报语法错 | 看 `logs/`；可能缺 bash 特性；Agent 会自动 debug 重试 |
| 想看 Agent 每一步 | 看 `storage/codeagent_jobs/<task_id>/logs/` |
