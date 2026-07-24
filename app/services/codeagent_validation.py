"""Path B 智能代码 Agent —— 验证工具（in-process MCP 工具）。

暴露 run_validation / validate_delivery 两个 in-process 工具给 Claude Agent SDK 会话。
ValidationJob 封装单任务的验证状态 + sandbox 执行（local 本机 / docker sge-master）。

设计要点：
- 每个 standalone 任务一个 ValidationJob（独立工作区 jobs/<task_id>/{input,code,output,logs}）。
- make_tools() 返回闭包绑定本 job 的 @tool 列表，供 create_sdk_mcp_server 注册（支持多 job 并发）。
- run_validation：bash -n → shellcheck(若可用) → sandbox 执行(INPUT_DIR/OUTPUT_DIR) →
  校验 output/result.json 与声明的产物。返回结构化 JSON（attempt/phase/stderr/script_sha256）。
- 硬限制：≤MAX_ATTEMPTS、脚本 sha256 必须变化（防空转烧 token）。
- validate_delivery 仅在 run_validation 最近一次 ok 时放行，且校验脚本 sha 与最近成功版本一致。

依赖：claude-agent-sdk（@tool）。后端 python3.13 需安装；P0 已在独立 venv 验证通过。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from claude_agent_sdk import tool

RUN_VALIDATION_DESC = (
    "验证 code/analysis.sh：1) bash -n 语法检查 2) shellcheck(若可用) "
    "3) 在沙箱执行(设置 INPUT_DIR/OUTPUT_DIR，只读 input 只写 output) "
    "4) 校验 output/result.json 与声明的产物。返回结构化 JSON(含 attempt/phase/stderr/script_sha256)。"
    "硬限制：最多 5 次，每次脚本 sha256 必须变化。失败时据此修改 code/analysis.sh 再试。"
)
VALIDATE_DELIVERY_DESC = (
    "仅当最近一次 run_validation 成功(ok=true)才允许调用。复核：最终脚本存在、"
    "sha256 与最近成功版本一致、result.json 与产物齐全。通过即视为可交付。"
)


class ValidationJob:
    """单任务的验证状态机 + sandbox 执行器。"""

    def __init__(self, job_dir, *, sandbox=None, container=None,
                 max_attempts=None, exec_timeout=None):
        # 延迟 import：让本模块可在无后端 env 的 venv 里单测
        from config.codeagent import (
            CODEAGENT_SANDBOX, CODEAGENT_SANDBOX_CONTAINER,
            CODEAGENT_MAX_ATTEMPTS, CODEAGENT_EXEC_TIMEOUT,
        )
        self.job_dir = Path(job_dir)
        self.code = self.job_dir / "code" / "analysis.sh"
        self.input_dir = self.job_dir / "input"
        self.output_dir = self.job_dir / "output"
        self.logs = self.job_dir / "logs"
        self.sandbox = sandbox or CODEAGENT_SANDBOX
        self.container = container or CODEAGENT_SANDBOX_CONTAINER
        self.max_attempts = max_attempts or CODEAGENT_MAX_ATTEMPTS
        self.exec_timeout = exec_timeout or CODEAGENT_EXEC_TIMEOUT
        self.attempt = 0
        self.last_sha: str | None = None
        self.last_ok = False
        self.history: list[dict] = []     # run_validation 记录
        self.delivery: list[dict] = []    # validate_delivery 记录（与 history 分开）

    @staticmethod
    def _sha(p: Path):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16] if Path(p).exists() else None

    def _finish(self, res: dict, ok: bool, *, is_error=False, kind="validation"):
        """统一收尾：记 history/delivery、写日志、返回 in-process 工具结果。"""
        res["ok"] = ok
        rec = {"attempt": res.get("attempt"), "sha": res.get("script_sha256"),
               "ok": ok, "phase": res.get("phase")}
        if kind == "validation":
            self.history.append(rec)
            self.last_ok = ok
        else:
            self.delivery.append(rec)
        self.logs.mkdir(parents=True, exist_ok=True)
        (self.logs / f"{kind}s.jsonl").open("a", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False) + "\n")
        return {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}],
                "is_error": is_error or (not ok)}

    # ─── sandbox 执行 ───────────────────────────────────────────────
    def _run_local(self, sp: Path):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "INPUT_DIR": str(self.input_dir), "OUTPUT_DIR": str(self.output_dir)}
        exe = subprocess.run(["bash", str(sp)], capture_output=True, text=True,
                             timeout=self.exec_timeout, env=env, cwd=str(self.job_dir))
        return exe.returncode, exe.stdout, exe.stderr, None

    def _run_docker(self, sp: Path):
        """docker exec <container> 执行。约定 job_dir 挂载到容器 /ws（P2 完善挂载+权限）。"""
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        cmd = ["docker", "exec", self.container, "bash", "-lc",
               f"INPUT_DIR=/ws/input OUTPUT_DIR=/ws/output "
               f"timeout {self.exec_timeout} bash /ws/code/analysis.sh"]
        exe = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=self.exec_timeout + 10)
        return exe.returncode, exe.stdout, exe.stderr, None

    def run_in_sandbox(self, sp: Path):
        try:
            return self._run_docker(sp) if self.sandbox == "docker" else self._run_local(sp)
        except subprocess.TimeoutExpired:
            return None, "", "", f"执行超时(>{self.exec_timeout}s)"
        except Exception as e:  # docker 不可用等
            return None, "", "", f"{type(e).__name__}: {e}"

    # ─── in-process 工具（闭包绑定 self）────────────────────────────
    def make_tools(self):
        async def run_validation(args):
            script = args.get("script", "code/analysis.sh")
            sp = self.job_dir / script
            res = {"tool": "run_validation", "sandbox": self.sandbox}

            if not sp.exists():
                return self._finish({**res, "error": f"脚本不存在: {script}"}, False, is_error=True)
            sha = self._sha(sp)
            if sha == self.last_sha:  # 防空转
                return self._finish(
                    {**res, "error": "脚本内容与上次相同(sha256 一致)，请实际修改后再验证。"},
                    False, is_error=True)
            if self.attempt >= self.max_attempts:
                return self._finish(
                    {**res, "error": f"已达最大验证次数 {self.max_attempts}，停止。"}, False, is_error=True)

            self.attempt += 1
            self.last_sha = sha
            res["attempt"] = self.attempt
            res["script_sha256"] = sha

            # 1) 语法
            syn = subprocess.run(["bash", "-n", str(sp)], capture_output=True, text=True)
            if syn.returncode != 0:
                return self._finish({**res, "phase": "syntax", "stderr": syn.stderr.strip()}, False)
            res["syntax_check"] = "passed"

            # 2) shellcheck（可选）
            if shutil.which("shellcheck"):
                sc = subprocess.run(["shellcheck", str(sp)], capture_output=True, text=True)
                res["shellcheck"] = "passed" if sc.returncode == 0 else "warnings"
                if sc.returncode != 0:
                    res["shellcheck_output"] = (sc.stdout + sc.stderr)[:600]

            # 3) 执行
            code_, out, err, emsg = self.run_in_sandbox(sp)
            if emsg:
                res["phase"] = "execution"
                res["stderr"] = emsg
                return self._finish(res, False)
            res["exit_code"] = code_
            res["stdout"] = out[-800:]
            res["stderr"] = err[-1200:]
            if code_ != 0:
                res["phase"] = "execution"
                return self._finish(res, False)

            # 4) 校验 result.json + 声明产物
            rj = self.output_dir / "result.json"
            if not rj.exists():
                return self._finish({**res, "phase": "output", "stderr": "缺少 output/result.json"}, False)
            try:
                rjd = json.loads(rj.read_text(encoding="utf-8"))
            except Exception as e:
                return self._finish({**res, "phase": "output", "stderr": f"result.json 解析失败: {e}"}, False)
            res["result_status"] = rjd.get("status")
            res["result_summary"] = rjd.get("summary")
            issues = []
            for o in (rjd.get("outputs") or []):
                p = self.output_dir / o.get("path", "")
                if not p.exists():
                    issues.append(f"声明产物缺失: {o.get('path')}")
                elif o.get("allow_empty") is False and p.stat().st_size == 0:
                    issues.append(f"声明产物为空: {o.get('path')}")
            if issues:
                res["phase"] = "output_check"
                res["validation_issues"] = issues
                return self._finish(res, False)

            return self._finish(res, True)

        async def validate_delivery(args):
            res = {"tool": "validate_delivery"}
            if not self.last_ok:
                return self._finish({**res, "error": "最近一次 run_validation 未通过，不能交付。"},
                                    False, is_error=True, kind="delivery")
            if not self.code.exists():
                return self._finish({**res, "error": "最终脚本不存在"}, False, is_error=True, kind="delivery")
            sha = self._sha(self.code)
            if sha != self.last_sha:
                return self._finish(
                    {**res, "error": "脚本 sha256 与最近成功验证版本不一致，请重新 run_validation。"},
                    False, is_error=True, kind="delivery")
            res["script_sha256"] = sha
            res["delivered"] = True
            return self._finish(res, True, kind="delivery")

        rv = tool("run_validation", RUN_VALIDATION_DESC, {"script": "code/analysis.sh"})(run_validation)
        vd = tool("validate_delivery", VALIDATE_DELIVERY_DESC, {})(validate_delivery)
        return [rv, vd]
