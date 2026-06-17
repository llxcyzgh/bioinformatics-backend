"""
编排脚本生成器：根据工具链生成 bash 编排脚本。
每个步骤调用独立的 sh 脚本，通过参数传递 input/output 文件。
"""

import os

from .script_registry import ScriptCallDef, COMMON_PRIMERS


def _extract_sample_name(filename: str) -> str:
    """从上传文件名提取样本名（去掉 .R1.fastq.gz / .R2.fastq.gz 等后缀）。"""
    import re
    # 去掉常见后缀模式
    for suffix in [".R1.fastq.gz", ".R2.fastq.gz", ".R1.fq.gz", ".R2.fq.gz",
                   ".fastq.gz", ".fq.gz", ".fastq", ".fq"]:
        if filename.endswith(suffix):
            return filename[: -len(suffix)]
    # 去掉扩展名
    return re.sub(r"\.[^.]+$", "", filename)


def _resolve_fastq_pair_uploads(file_mappings: list[dict], required_files: list[dict]) -> dict:
    """
    解析 FASTQ_PAIR 上传文件，返回 {sample_name: {"R1": path, "R2": path}}。
    file_mappings: [{"slot_label": ..., "original_name": ..., "stored_name": ...}]
    """
    samples: dict[str, dict[str, str]] = {}
    for fm in file_mappings:
        name = fm.get("original_name", "")
        slot = fm.get("slot_label", "")
        stored = fm.get("stored_name", name)
        # 判断是 R1 还是 R2
        is_r1 = any(kw in name.upper() for kw in ["R1", "_R1", ".R1"])
        is_r2 = any(kw in name.upper() for kw in ["R2", "_R2", ".R2"])
        if is_r1 or is_r2:
            sample = _extract_sample_name(name)
            if sample not in samples:
                samples[sample] = {}
            if is_r1:
                samples[sample]["R1"] = stored
            else:
                samples[sample]["R2"] = stored
    return samples


def generate_orchestrator_script(
    tool_ids: list[str],
    call_defs: dict[str, ScriptCallDef],
    tool_names: dict[str, str],
    file_mappings: list[dict],
    required_files: list[dict],
    extra_params: dict | None = None,
    task_id: int | None = None,
    param_overrides: dict | None = None,
) -> str:
    """
    生成编排脚本。

    Args:
        tool_ids: 工具链中的 tool_id 列表（按顺序）
        call_defs: tool_id -> ScriptCallDef（脚本路径/参数/输出，由领域从 DB 构造）
        tool_names: tool_id -> 显示名（由领域从 DB 构造）
        file_mappings: 上传文件映射 [{"slot_label", "original_name", "stored_name", "file_id"}]
        required_files: resolve_required_files() 返回的文件需求列表
        extra_params: 额外参数 {"primer_f", "primer_r", "metadata_file", "group_list"}
        task_id: 任务 ID，用于生成日志标识
        param_overrides: 用户在节点上改的参数 {tool_id: {flag: value}}，
            只含白名单内、已通过校验的 _CONFIG 值；覆盖各工具 .sh 的默认值。

    Returns:
        生成的 bash 编排脚本字符串
    """
    extra = extra_params or {}

    # ─── 解析用户上传文件 ───
    uploaded_files: dict[str, str] = {}  # data_type -> stored file path
    for rf in required_files:
        type_id = rf.get("typeId", "")
        # 找到匹配的上传文件
        for fm in file_mappings:
            slot = fm.get("slot_label", "")
            stored = fm.get("stored_name", fm.get("original_name", ""))
            if slot == rf.get("label", "") or type_id in slot:
                uploaded_files[type_id] = f"/shared/{stored}"

    # 特殊处理 FASTQ_PAIR: 拆分为 R1/R2
    samples = _resolve_fastq_pair_uploads(file_mappings, required_files)
    if samples:
        first_sample = next(iter(samples.values()))
        if "R1" in first_sample:
            uploaded_files["FASTQ_R1"] = f"/shared/{first_sample['R1']}"
        if "R2" in first_sample:
            uploaded_files["FASTQ_R2"] = f"/shared/{first_sample['R2']}"
        uploaded_files["_SAMPLES"] = str(samples)  # 暂存样本信息

    # 元数据文件
    metadata_stored = extra.get("metadata_stored", "")
    if metadata_stored:
        uploaded_files["_METADATA"] = f"/shared/{metadata_stored}"

    # ─── 开始生成脚本 ───
    lines: list[str] = []

    # Header
    lines.append("#!/bin/bash")
    lines.append("# BioFlow 自动生成编排脚本")
    lines.append("# 工具链: " + " → ".join(
        tool_names.get(tid, tid) for tid in tool_ids
    ))
    # SGE 并行环境（可选）：设了 BIOFLOW_SGE_PE（如 "make 8"）才申请多 slot。
    # 否则单 slot、bash & 仍并发但时分复用。需与 BIOFLOW_MAX_PARALLEL 配套。
    pe = os.getenv("BIOFLOW_SGE_PE", "").strip()
    if pe:
        lines.append(f"#$ -pe {pe}")
    lines.append("")
    lines.append("set -euo pipefail")
    lines.append("")
    lines.append('export PATH=/opt/conda/bin:$PATH')
    lines.append('export AMPLICON_ROOT="/opt/amplicon"')
    if task_id is not None:
        lines.append("")
        lines.append(f'# Task log: /shared/task_{task_id}.log')
        lines.append('_log() { echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] [$1] $2"; }')
    lines.append("")

    # 用户上传文件变量
    lines.append("# ─── 用户上传文件 ───")
    for rf in required_files:
        type_id = rf.get("typeId", "")
        label = rf.get("label", "")
        if type_id == "FASTQ_PAIR":
            # FASTQ 对会在下面 per-sample 循环中处理
            if samples:
                first = next(iter(samples.values()))
                if "R1" in first:
                    lines.append(f'FASTQ_R1="/shared/{first["R1"]}"')
                if "R2" in first:
                    lines.append(f'FASTQ_R2="/shared/{first["R2"]}"')
        else:
            path = uploaded_files.get(type_id, "")
            if path:
                var_name = type_id.replace("-", "_")
                lines.append(f'{var_name}="{path}"')
    if metadata_stored:
        lines.append(f'METADATA="/shared/{metadata_stored}"')
    lines.append("")

    # ─── 跟踪已生成的文件 ───
    produced_files: dict[str, str] = {}  # data_type → file path
    # 初始化用户上传的根输入
    for rf in required_files:
        type_id = rf.get("typeId", "")
        if type_id != "FASTQ_PAIR" and type_id in uploaded_files:
            produced_files[type_id] = uploaded_files[type_id]

    step_num = 0
    total_steps = len(tool_ids)

    i = 0
    while i < len(tool_ids):
        tool_id = tool_ids[i]
        call_def = call_defs.get(tool_id)
        tool_name = tool_names.get(tool_id, tool_id)

        if not call_def:
            lines.append(f"# ⚠ 未找到 {tool_id} 的脚本注册，跳过")
            lines.append("")
            i += 1
            continue

        # ─── 连续 per-sample 工具 → 合并成一个跨样本并行区 ───
        if call_def.per_sample:
            region: list[str] = []
            while i < len(tool_ids):
                cd = call_defs.get(tool_ids[i])
                if cd and cd.per_sample:
                    region.append(tool_ids[i])
                    i += 1
                else:
                    break
            step_num = _gen_parallel_region(
                lines, region, call_defs, tool_names, samples, extra,
                produced_files, step_num, total_steps, task_id, param_overrides,
            )
            for tid in region:
                _register_region_outputs(tid, call_defs, produced_files)
            continue

        # ─── 非 per-sample（dada2 / 通用）: 单次执行，天然在并行区的 wait 之后 ───
        step_num += 1
        tool_overrides = (param_overrides or {}).get(tool_id, {})
        _emit_step_header(lines, step_num, total_steps, tool_name, task_id)
        if tool_id == "amp-dada2":
            # DADA2 需要 manifest，先生成 manifest 再调用
            _gen_dada2_step(lines, call_def, samples, produced_files, step_num, task_id, tool_overrides)
        else:
            if task_id is not None:
                lines.append(f'_log "INFO" "Step {step_num}/{total_steps}: {tool_name} 执行中"')
            lines.append(_build_single_command(call_def, produced_files, extra, tool_overrides))
        for out in call_def.outputs:
            produced_files[out.data_type] = out.filename.replace("${sample}", "")
        _emit_step_footer(lines, step_num, total_steps, tool_name, task_id)
        i += 1

    return "\n".join(lines) + "\n"


def _config_flags(tool_overrides: dict, specs: list[tuple[str, str]]) -> list[str]:
    """按白名单 specs=[(flag, default)] 生成 config 参数串（override 优先；空值跳过）。

    只输出经核实的 .sh 接受的 flag——per-sample .sh 用 `*) exit 1` 兜底，未知 flag 会崩。
    """
    out: list[str] = []
    for flag, default in specs:
        val = tool_overrides.get(flag, default)
        if val is None or val == "":
            continue
        out.append(f"{flag} {val}")
    return out


def _emit_call(lines: list[str], script_path: str, args: list[str]) -> None:
    """输出 `bash <path> arg1 ... `，反斜杠续行（首行 2 空格缩进，续行 4 空格）。"""
    if not args:
        lines.append(f'  bash ${{AMPLICON_ROOT}}/{script_path}')
        return
    lines.append(f'  bash ${{AMPLICON_ROOT}}/{script_path} \\')
    last = len(args) - 1
    for i, a in enumerate(args):
        sep = " \\" if i < last else ""
        lines.append(f'    {a}{sep}')


def _gen_cutadapt_body(lines, call_def, extra: dict, tool_overrides: dict,
                       step_num: int, task_id: int | None, indent: str = ""):
    """单个样本的 Cutadapt 片段（不含 for/done/SAMPLES，供并行区子shell调用）。"""
    primer_f = extra.get("primer_f", COMMON_PRIMERS["16S V3-V4"]["f"])
    primer_r = extra.get("primer_r", COMMON_PRIMERS["16S V3-V4"]["r"])
    lines.append(f'{indent}R1_FILE="/shared/${{SAMPLE}}.R1.fastq.gz"')
    lines.append(f'{indent}R2_FILE="/shared/${{SAMPLE}}.R2.fastq.gz"')
    lines.append(f'{indent}for f in /shared/${{SAMPLE}}*.R1*; do R1_FILE="$f"; break; done')
    lines.append(f'{indent}for f in /shared/${{SAMPLE}}*.R2*; do R2_FILE="$f"; break; done')
    if task_id is not None:
        lines.append(f'{indent}_log "INFO" "Step {step_num}: cutadapt ${{SAMPLE}}"')
    args = [
        '-r1 "${R1_FILE}"',
        '-r2 "${R2_FILE}"',
        f'-f "{primer_f}"',
        f'-r "{primer_r}"',
    ]
    args += _config_flags(tool_overrides, [("-e", "0.1"), ("-l", "100"), ("-n", "1")])
    _emit_call(lines, call_def.script_path, args)


def _gen_flash_body(lines, call_def, tool_overrides: dict,
                    step_num: int, task_id: int | None, indent: str = ""):
    """单个样本的 FLASH 片段。"""
    lines.append(f'{indent}TRIMMED_R1="${{SAMPLE}}.cutadapt.R1.fastq.gz"')
    lines.append(f'{indent}TRIMMED_R2="${{SAMPLE}}.cutadapt.R2.fastq.gz"')
    if task_id is not None:
        lines.append(f'{indent}_log "INFO" "Step {step_num}: FLASH ${{SAMPLE}}"')
    args = ['-1 "${TRIMMED_R1}"', '-2 "${TRIMMED_R2}"']
    args += _config_flags(tool_overrides, [("-m", "10"), ("-M", "250"), ("-x", "0.1"), ("-t", "1")])
    _emit_call(lines, call_def.script_path, args)


def _gen_frags_qc_body(lines, call_def, tool_overrides: dict,
                       step_num: int, task_id: int | None, indent: str = ""):
    """单个样本的 Frags QC 片段。"""
    lines.append(f'{indent}MERGED="${{SAMPLE}}.out.extendedFrags.fastq"')
    if task_id is not None:
        lines.append(f'{indent}_log "INFO" "Step {step_num}: Frags QC ${{SAMPLE}}"')
    args = ['-i "${MERGED}"']
    args += _config_flags(tool_overrides, [("-q", "19"), ("-u", "15"), ("-d", "")])
    _emit_call(lines, call_def.script_path, args)


def _register_region_outputs(tool_id: str, call_defs: dict, produced: dict) -> None:
    """注册 per-sample 区工具输出（装饰性：dada2 直接读 samples，不读 produced）。"""
    cd = call_defs.get(tool_id)
    if not cd:
        return
    for out in cd.outputs:
        produced[out.data_type] = out.filename.replace("${sample}", "")


def _emit_step_header(lines, step_num: int, total_steps: int, tool_name: str, task_id) -> None:
    lines.append(f"# ─── Step {step_num}/{total_steps}: {tool_name} ───")
    if task_id is not None:
        lines.append(f'_log "INFO" "Step {step_num}/{total_steps}: {tool_name} 开始"')
    else:
        lines.append(f'echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] [Step {step_num}/{total_steps}] {tool_name}..."')


def _emit_step_footer(lines, step_num: int, total_steps: int, tool_name: str, task_id) -> None:
    if task_id is not None:
        lines.append(f'_log "INFO" "Step {step_num}/{total_steps}: {tool_name} 完成"')
    else:
        lines.append(f'echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] Step {step_num} 完成"')
    lines.append("")


def _gen_parallel_region(lines, region_ids: list[str], call_defs: dict, tool_names: dict,
                         samples: dict, extra: dict, produced: dict,
                         step_num: int, total_steps: int, task_id, param_overrides) -> int:
    """把连续的 per-sample 工具合并成一个跨样本并行区。

    每个样本在后台子shell内按序跑完整条链（cutadapt→flash→frags_qc，文件名依赖决定顺序），
    跨样本并行；显式 wait 屏障后再由调用方跑 dada2 等汇合步骤。返回新的 step_num。
    """
    start = step_num + 1
    end = step_num + len(region_ids)
    label = " → ".join(tool_names.get(t, t) for t in region_ids)
    lines.append(f"# ─── Step {start}-{end}/{total_steps}: {label}（per-sample 并行） ───")
    if task_id is not None:
        lines.append(f'_log "INFO" "Steps {start}-{end}/{total_steps}: 并行预处理开始"')
    else:
        lines.append(f'echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] [Steps {start}-{end}/{total_steps}] 并行预处理..."')

    lines.append("SAMPLES=({})".format(" ".join(f'"{s}"' for s in samples.keys())))
    lines.append('MAX_JOBS="${BIOFLOW_MAX_PARALLEL:-4}"')
    lines.append('if [ "$MAX_JOBS" -lt 1 ] 2>/dev/null; then MAX_JOBS=1; fi')
    lines.append("_JOB_I=0")
    lines.append('for SAMPLE in "${SAMPLES[@]}"; do')
    lines.append("  (")
    for idx, tid in enumerate(region_ids):
        cd = call_defs.get(tid)
        ov = (param_overrides or {}).get(tid, {})
        s = step_num + idx + 1
        if tid == "amp-cutadapt":
            _gen_cutadapt_body(lines, cd, extra, ov, s, task_id, indent="    ")
        elif tid == "amp-flash":
            _gen_flash_body(lines, cd, ov, s, task_id, indent="    ")
        elif tid == "amp-frags-qc":
            _gen_frags_qc_body(lines, cd, ov, s, task_id, indent="    ")
        else:
            raise ValueError(f"per_sample 工具 {tid} 没有对应 body 生成器")
    lines.append("  ) &")
    lines.append("  _JOB_I=$((_JOB_I+1))")
    lines.append('  if [ $((_JOB_I % MAX_JOBS)) -eq 0 ]; then wait || { echo "[FATAL] per-sample step failed" >&2; exit 1; }; fi')
    lines.append("done")
    lines.append('wait || { echo "[FATAL] per-sample step failed" >&2; exit 1; }')
    if task_id is not None:
        lines.append(f'_log "INFO" "Steps {start}-{end}/{total_steps}: 并行预处理完成"')
    else:
        lines.append(f'echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] Steps {start}-{end} 完成"')
    lines.append("")
    return end


def _gen_dada2_step(
    lines: list[str], call_def, samples: dict, produced: dict,
    step_num: int, task_id: int | None, tool_overrides: dict,
):
    """生成 DADA2 步骤，包括 manifest 生成。"""
    lines.append("# 生成 manifest 文件")
    lines.append('echo -e "sample-id\\tabsolute-filepath" > manifest.tsv')
    if samples:
        for sample_name in samples:
            # 使用 QC 后的 fastq 文件
            lines.append(f'echo -e "{sample_name}\\t$(pwd)/{sample_name}.fastq" >> manifest.tsv')
    else:
        lines.append("# ⚠ 未检测到样本，需手动编辑 manifest.tsv")
    lines.append("")
    if task_id is not None:
        lines.append(f'_log "INFO" "Step {step_num}: DADA2 开始"')
    args = ['-m manifest.tsv']
    args += _config_flags(tool_overrides, [("-t", "0"), ("-n", "12"), ("-a", "1")])
    _emit_call(lines, call_def.script_path, args)
    if task_id is not None:
        lines.append(f'_log "INFO" "Step {step_num}: DADA2 完成"')

    produced["FEATURE_SEQS"] = "featureSeqs.qza"
    produced["FEATURE_TABLE"] = "featureTable.biom"
    produced["FEATURE_FASTA"] = "feature.fasta"


def _build_single_command(call_def, produced: dict, extra: dict, tool_overrides: dict | None = None) -> str:
    """为通用工具构建单条 bash 命令。"""
    tool_overrides = tool_overrides or {}
    cmd_parts = [f"bash ${{AMPLICON_ROOT}}/{call_def.script_path}"]

    for param in call_def.params:
        dt = param.data_type

        if dt == "_CONFIG":
            # 用户在节点上改的值优先（已通过 confirm_upload 正则校验），否则用 .md 默认
            value = tool_overrides.get(param.flag, param.default)
            if value:
                cmd_parts.append(f'{param.flag} {value}')
            continue

        if dt == "_PRIMER_F":
            primer_f = extra.get("primer_f", COMMON_PRIMERS["16S V3-V4"]["f"])
            cmd_parts.append(f'{param.flag} "{primer_f}"')
            continue

        if dt == "_PRIMER_R":
            primer_r = extra.get("primer_r", COMMON_PRIMERS["16S V3-V4"]["r"])
            cmd_parts.append(f'{param.flag} "{primer_r}"')
            continue

        if dt == "_MANIFEST":
            cmd_parts.append(f'{param.flag} manifest.tsv')
            continue

        if dt == "_METADATA":
            meta = produced.get("_METADATA", extra.get("metadata_stored", ""))
            if meta:
                cmd_parts.append(f'{param.flag} "{meta}"')
            elif not param.required:
                continue
            continue

        if dt == "_GROUP_LIST":
            # group.list 通常由 metadata 生成
            cmd_parts.append(f'{param.flag} group.list')
            continue

        if dt.startswith("_"):
            # 其他特殊类型跳过
            if param.default:
                cmd_parts.append(f'{param.flag} {param.default}')
            continue

        # 普通数据类型 → 从 produced_files 中查找
        if dt in produced:
            cmd_parts.append(f'{param.flag} "{produced[dt]}"')
        elif param.required:
            cmd_parts.append(f'{param.flag} "<{dt}>"')
        # optional 且没有找到 → 跳过

    # 格式化命令
    if len(cmd_parts) <= 2:
        return " ".join(cmd_parts)

    first = cmd_parts[0]
    rest = cmd_parts[1:]
    formatted = first + " \\\n  " + " \\\n  ".join(rest)
    return formatted
