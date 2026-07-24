"""Path B 智能代码 Agent 编排：建工作区 → profiler → 起 SDK 会话(挂验证工具) → 收验证过的脚本。

替代 StandaloneScriptService._generate 的一次性盲生成。关键：在**上传后**(confirm_upload，
真实文件就绪)调用，让 Agent 拿真实数据走"生成→run_validation→读错误→改→再验证→交付"闭环。

run() 返回与 _generate 同结构的 gen dict（{sh_content, outputs, language, slug, aliases} + 额外
validation_report/attempts），可直接喂 _archive 归档（_archive 仅需 ext 支持 bash）。

依赖：claude-agent-sdk（后端 python3.13 需安装）。凭证通过 CODEAGENT_SDK_ENV 注入 SDK 子进程，
不复用 zjiaai 登录态。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import shutil
from pathlib import Path

from claude_agent_sdk import (
    query, ClaudeAgentOptions, create_sdk_mcp_server,
    AssistantMessage, ResultMessage, ToolUseBlock,
)

from app.services.codeagent_validation import ValidationJob
from app.services.codeagent_profiler import profile_files
from config.codeagent import (
    CODEAGENT_MAX_TURNS, CODEAGENT_MODEL, CODEAGENT_JOBS_ROOT,
    CODEAGENT_ALLOWED_TOOLS, CODEAGENT_MCP_SERVER, CODEAGENT_SDK_ENV,
)

logger = logging.getLogger(__name__)

# 用 __X__ 命名占位 + replace，避免 profiles JSON 的 {} 与 str.format 冲突
_SYSTEM_PROMPT = """你是 BioFlow 的生信脚本生成助手。分析类型：__ANALYSIS_TYPE__

严格合同（code/analysis.sh 必须遵守）：
- 以 `#!/usr/bin/env bash` + `set -Eeuo pipefail` 开头；
- 校验 INPUT_DIR="${INPUT_DIR:?INPUT_DIR is required}" / OUTPUT_DIR="${OUTPUT_DIR:?OUTPUT_DIR is required}"，并 `mkdir -p "$OUTPUT_DIR"`；
- 只从 $INPUT_DIR 读、只向 $OUTPUT_DIR 写，不改原始输入、不联网、不装依赖；
- 对路径和变量加引号；失败非零退出；
- 内部按需调 Rscript / python3（运行时偏好：__RUNTIME__）；
- 最后用 heredoc 写出 $OUTPUT_DIR/result.json，含 status(success/failed)、summary、outputs[{path,allow_empty}]。

输入数据要求：
__REQUIREMENTS__
参数：__PARAMS__

输入数据真实画像（列名/类型/行数/预览，务必据此用对列名与格式，不要猜）：
__PROFILES__

流程：先用 Read 看清 input/ 下真实文件 → Write 写 code/analysis.sh → 调 run_validation 验证 →
若失败，仔细读返回 JSON 的 phase/stderr/validation_issues，Edit 修改 code/analysis.sh 后再 run_validation
（每次脚本内容必须实际变化）→ run_validation 成功后调 validate_delivery 完成交付。
一切以 run_validation 的机器结果为准，不要凭空声称"应该能跑"。"""


class StandaloneCodeAgent:
    """生成 + 验证 + debug 闭环的编排器。"""

    @staticmethod
    def run(analysis_type: str, data_requirements: list[dict], params: list[dict],
            runtime_hint: str, content: str, staged_files: dict, job_id: str,
            *, jobs_root: str | None = None) -> dict | None:
        """同步入口（供 chat_service 同步方法调用）。

        staged_files: {key: 真实文件绝对路径}（confirm_upload 后的上传文件）。
        返回 gen dict（验证过的脚本信息，喂 _archive），失败返回 None。
        """
        jobs_root = jobs_root or CODEAGENT_JOBS_ROOT
        job_dir = Path(jobs_root) / str(job_id)
        try:
            return asyncio.run(StandaloneCodeAgent._run_async(
                job_dir, analysis_type, data_requirements, params, runtime_hint, content, staged_files))
        except Exception as e:
            logger.error(f"[CodeAgent] run 失败 job={job_id}: {type(e).__name__}: {e}")
            return None

    @staticmethod
    async def _run_async(job_dir: Path, analysis_type, data_requirements, params,
                         runtime_hint, content, staged_files) -> dict | None:
        # 1) 工作区 + 软链真实上传文件到 input/
        StandaloneCodeAgent._setup_workspace(job_dir, data_requirements, staged_files)
        # 2) profiler（画像喂 Agent）
        profiles = profile_files(job_dir / "input")
        (job_dir / "profiles.json").write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
        # 3) 验证工具（in-process，闭包绑本 job）
        vj = ValidationJob(job_dir)
        srv = create_sdk_mcp_server(CODEAGENT_MCP_SERVER, "1.0.0", vj.make_tools())
        # 4) prompt + options
        system = StandaloneCodeAgent._build_system_prompt(
            analysis_type, data_requirements, params, runtime_hint, profiles)
        task = (f"【分析任务】{analysis_type}\n【用户原话】{content}\n"
                f"请用 input/ 下的真实数据完成分析，结果写 output/，并生成 output/result.json。")
        opts_kwargs = dict(
            system_prompt=system,
            cwd=str(job_dir),
            tools=list(CODEAGENT_ALLOWED_TOOLS),
            allowed_tools=list(CODEAGENT_ALLOWED_TOOLS) + [
                f"mcp__{CODEAGENT_MCP_SERVER}__run_validation",
                f"mcp__{CODEAGENT_MCP_SERVER}__validate_delivery",
            ],
            permission_mode="dontAsk",
            mcp_servers={CODEAGENT_MCP_SERVER: srv},
            max_turns=CODEAGENT_MAX_TURNS,
            env=dict(CODEAGENT_SDK_ENV),
        )
        if CODEAGENT_MODEL:
            opts_kwargs["model"] = CODEAGENT_MODEL
        opts = ClaudeAgentOptions(**opts_kwargs)

        # 5) 跑会话
        logger.info(f"[CodeAgent] 起会话 job={job_dir.name} files={list(staged_files)}")
        async for msg in query(prompt=task, options=opts):
            if isinstance(msg, AssistantMessage):
                for b in msg.content:
                    if isinstance(b, ToolUseBlock):
                        logger.info(f"[CodeAgent] tool_use {b.name}({json.dumps(b.input, ensure_ascii=False)[:120]})")
            elif isinstance(msg, ResultMessage):
                logger.info(f"[CodeAgent] result turns={msg.num_turns} err={msg.is_error} "
                            f"reason={getattr(msg, 'terminal_reason', None)}")

        # 6) 收验证过的脚本
        return StandaloneCodeAgent._collect(vj, job_dir, analysis_type)

    # ─── 组装 ──────────────────────────────────────────────────────
    @staticmethod
    def _setup_workspace(job_dir: Path, data_requirements, staged_files):
        if job_dir.exists():
            shutil.rmtree(job_dir)
        for d in ("input", "code", "output", "logs", "delivery"):
            (job_dir / d).mkdir(parents=True, exist_ok=True)
        # 按 data_requirements 的 key 把真实文件软链到 input/<key>.<ext>
        for req in (data_requirements or []):
            key = req.get("key")
            if not key:
                continue
            src = (staged_files or {}).get(key)
            if src and os.path.exists(src):
                ext = Path(src).suffix or ".csv"
                dst = job_dir / "input" / f"{key}{ext}"
                try:
                    os.symlink(os.path.abspath(src), dst)
                except OSError:
                    shutil.copy(src, dst)  # 软链失败（跨设备等）则复制

    @staticmethod
    def _build_system_prompt(analysis_type, data_requirements, params, runtime_hint, profiles) -> str:
        req_lines = []
        for d in (data_requirements or []):
            cols = ", ".join(d.get("columns") or []) or "未指定"
            req_lines.append(
                f"- {d.get('label')}（文件 input/{d.get('key')}<.csv/.tsv>，关键列: {cols}；{d.get('columns_desc') or ''}）")
        req_text = "\n".join(req_lines) or "（按 input/ 下实际文件处理）"
        param_text = "; ".join(f"{p.get('label')}={p.get('default')!r}" for p in (params or [])) or "无"
        prof_text = json.dumps(profiles, ensure_ascii=False, indent=2) if profiles else "（无）"
        return (_SYSTEM_PROMPT
                .replace("__ANALYSIS_TYPE__", str(analysis_type or "独立分析"))
                .replace("__RUNTIME__", str(runtime_hint or "bash（可调 Rscript/python3）"))
                .replace("__REQUIREMENTS__", req_text)
                .replace("__PARAMS__", param_text)
                .replace("__PROFILES__", prof_text))

    @staticmethod
    def _collect(vj: ValidationJob, job_dir: Path, analysis_type) -> dict | None:
        """收验证过的 analysis.sh + validation_report，组装 gen dict。未验证通过 → None。"""
        sh_path = job_dir / "code" / "analysis.sh"
        if not vj.last_ok or not sh_path.exists():
            logger.warning(f"[CodeAgent] 未拿到验证过的脚本 attempts={vj.attempt} history={vj.history}")
            return None
        sh = sh_path.read_text(encoding="utf-8")

        # outputs 从 result.json 推
        outputs = []
        rj = job_dir / "output" / "result.json"
        if rj.exists():
            try:
                rjd = json.loads(rj.read_text(encoding="utf-8"))
                outputs = [{"filename": f"output/{o.get('path')}", "desc": str(o.get('path'))}
                           for o in (rjd.get("outputs") or []) if isinstance(o, dict)]
            except Exception:
                pass

        # slug（ascii 短横线 + 短哈希防碰撞，符合 _SLUG_RE）
        base = re.sub(r"[^a-z0-9]+", "-", (analysis_type or "standalone").lower()).strip("-")[:34] or "gen"
        slug = f"{base}-{hashlib.md5((analysis_type or '').encode('utf-8')).hexdigest()[:6]}"

        report = {"attempts": vj.attempt, "history": vj.history,
                  "delivery": vj.delivery, "sandbox": vj.sandbox}
        (job_dir / "delivery" / "validation_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        shutil.copy(sh_path, job_dir / "delivery" / "analysis.sh")

        logger.info(f"[CodeAgent] 交付 attempts={vj.attempt} slug={slug}")
        return {
            "sh_content": sh,
            "outputs": outputs,
            "language": "bash",
            "slug": slug,
            "aliases": [],  # Agent 不产别名；召回降级，P3 让 Agent 补或从 analysis_type 推
            "validation_report": report,
            "attempts": vj.attempt,
        }
