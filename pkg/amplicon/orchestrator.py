"""
编排脚本生成器：根据工具链生成 bash 编排脚本。
每个步骤调用独立的 sh 脚本，通过参数传递 input/output 文件。
"""

from .script_registry import get_script_call, COMMON_PRIMERS
from .amplicon_tools import get_all_tools, resolve_root_inputs, DATA_TYPE_TO_FILE_REQUIREMENT


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
    file_mappings: list[dict],
    required_files: list[dict],
    extra_params: dict | None = None,
    task_id: int | None = None,
) -> str:
    """
    生成编排脚本。

    Args:
        tool_ids: 工具链中的 tool_id 列表（按顺序）
        file_mappings: 上传文件映射 [{"slot_label", "original_name", "stored_name", "file_id"}]
        required_files: resolve_root_inputs() 返回的文件需求列表
        extra_params: 额外参数 {"primer_f", "primer_r", "metadata_file", "group_list"}
        task_id: 任务 ID，用于生成日志标识

    Returns:
        生成的 bash 编排脚本字符串
    """
    extra = extra_params or {}
    tool_map = {t.id: t for t in get_all_tools()}

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
        tool_map.get(tid, type("Obj", (), {"name": tid})).name for tid in tool_ids
    ))
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

    for tool_id in tool_ids:
        call_def = get_script_call(tool_id)
        tool_info = tool_map.get(tool_id)
        tool_name = tool_info.name if tool_info else tool_id

        if not call_def:
            lines.append(f"# ⚠ 未找到 {tool_id} 的脚本注册，跳过")
            lines.append("")
            continue

        step_num += 1
        lines.append(f"# ─── Step {step_num}/{total_steps}: {tool_name} ───")
        if task_id is not None:
            lines.append(f'_log "INFO" "Step {step_num}/{total_steps}: {tool_name} 开始"')
        else:
            lines.append(f'echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] [Step {step_num}/{total_steps}] {tool_name}..."')

        # ─── 特殊处理: per-sample 步骤 ───
        if call_def.per_sample and tool_id == "amp-cutadapt":
            _gen_cutadapt_loop(lines, call_def, samples, extra, produced_files, step_num, task_id)
        elif call_def.per_sample and tool_id == "amp-flash":
            _gen_flash_loop(lines, call_def, samples, produced_files, step_num, task_id)
        elif call_def.per_sample and tool_id == "amp-frags-qc":
            _gen_frags_qc_loop(lines, call_def, samples, produced_files, step_num, task_id)
        elif tool_id == "amp-dada2":
            # DADA2 需要 manifest，先生成 manifest 再调用
            _gen_dada2_step(lines, call_def, samples, produced_files, step_num, task_id)
        else:
            # 通用步骤
            if task_id is not None:
                lines.append(f'_log "INFO" "Step {step_num}/{total_steps}: {tool_name} 执行中"')
            cmd = _build_single_command(call_def, produced_files, extra)
            lines.append(cmd)

        # 注册输出
        for out in call_def.outputs:
            fname = out.filename.replace("${sample}", "")
            produced_files[out.data_type] = fname

        if task_id is not None:
            lines.append(f'_log "INFO" "Step {step_num}/{total_steps}: {tool_name} 完成"')
        else:
            lines.append(f'echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] Step {step_num} 完成"')
        lines.append("")

    return "\n".join(lines) + "\n"


def _gen_cutadapt_loop(
    lines: list[str], call_def, samples: dict, extra: dict, produced: dict, step_num: int, task_id: int | None
):
    """生成 Cutadapt per-sample 循环。"""
    primer_f = extra.get("primer_f", COMMON_PRIMERS["16S V3-V4"]["f"])
    primer_r = extra.get("primer_r", COMMON_PRIMERS["16S V3-V4"]["r"])

    lines.append("SAMPLES=({})".format(
        " ".join(f'"{s}"' for s in samples.keys())
    ))
    lines.append("for SAMPLE in \"${SAMPLES[@]}\"; do")
    lines.append("  R1_FILE=\"/shared/${SAMPLE}.R1.fastq.gz\"")
    lines.append("  R2_FILE=\"/shared/${SAMPLE}.R2.fastq.gz\"")
    lines.append("  # 查找实际文件名")
    lines.append("  for f in /shared/${SAMPLE}*.R1*; do R1_FILE=\"$f\"; break; done")
    lines.append("  for f in /shared/${SAMPLE}*.R2*; do R2_FILE=\"$f\"; break; done")
    if task_id is not None:
        lines.append(f'  _log "INFO" "Step {step_num}: cutadapt 开始处理样本 ${{SAMPLE}}"')
    else:
        lines.append('  echo "  处理样本: ${SAMPLE}"')
    lines.append(f'  bash ${{AMPLICON_ROOT}}/{call_def.script_path} \\')
    lines.append('    -r1 "${R1_FILE}" \\')
    lines.append('    -r2 "${R2_FILE}" \\')
    lines.append(f'    -f "{primer_f}" \\')
    lines.append(f'    -r "{primer_r}"')
    if task_id is not None:
        lines.append(f'  _log "INFO" "Step {step_num}: cutadapt 完成处理样本 ${{SAMPLE}}"')
    lines.append("done")
    lines.append("")

    # 注册输出
    # Cutadapt 的输出会在当前目录下，DADA2 的 manifest 会引用它们
    first_sample = next(iter(samples.keys())) if samples else "sample"
    produced["TRIMMED_R1"] = f"${{{first_sample}}}.cutadapt.R1.fastq.gz"
    produced["TRIMMED_R2"] = f"${{{first_sample}}}.cutadapt.R2.fastq.gz"


def _gen_flash_loop(
    lines: list[str], call_def, samples: dict, produced: dict, step_num: int, task_id: int | None
):
    """生成 FLASH per-sample 循环。"""
    lines.append("for SAMPLE in \"${SAMPLES[@]}\"; do")
    lines.append("  TRIMMED_R1=\"${SAMPLE}.cutadapt.R1.fastq.gz\"")
    lines.append("  TRIMMED_R2=\"${SAMPLE}.cutadapt.R2.fastq.gz\"")
    if task_id is not None:
        lines.append(f'  _log "INFO" "Step {step_num}: FLASH 开始合并样本 ${{SAMPLE}}"')
    else:
        lines.append('  echo "  FLASH 合并: ${SAMPLE}"')
    lines.append(f'  bash ${{AMPLICON_ROOT}}/{call_def.script_path} \\')
    lines.append('    -1 "${TRIMMED_R1}" \\')
    lines.append('    -2 "${TRIMMED_R2}"')
    if task_id is not None:
        lines.append(f'  _log "INFO" "Step {step_num}: FLASH 完成合并样本 ${{SAMPLE}}"')
    lines.append("done")
    first_sample = next(iter(samples.keys())) if samples else "sample"
    produced["FASTQ_MERGED"] = f"${{{first_sample}}}.out.extendedFrags.fastq"


def _gen_frags_qc_loop(
    lines: list[str], call_def, samples: dict, produced: dict, step_num: int, task_id: int | None
):
    """生成 Frags QC per-sample 循环。"""
    lines.append("for SAMPLE in \"${SAMPLES[@]}\"; do")
    lines.append("  MERGED=\"${SAMPLE}.out.extendedFrags.fastq\"")
    if task_id is not None:
        lines.append(f'  _log "INFO" "Step {step_num}: Frags QC 开始处理样本 ${{SAMPLE}}"')
    else:
        lines.append('  echo "  质控: ${SAMPLE}"')
    lines.append(f'  bash ${{AMPLICON_ROOT}}/{call_def.script_path} \\')
    lines.append('    -i "${MERGED}"')
    if task_id is not None:
        lines.append(f'  _log "INFO" "Step {step_num}: Frags QC 完成处理样本 ${{SAMPLE}}"')
    lines.append("done")
    first_sample = next(iter(samples.keys())) if samples else "sample"
    produced["FASTQ_QC"] = f"${{{first_sample}}}.fastq"


def _gen_dada2_step(
    lines: list[str], call_def, samples: dict, produced: dict, step_num: int, task_id: int | None
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
    lines.append(f'bash ${{AMPLICON_ROOT}}/{call_def.script_path} \\')
    lines.append('  -m manifest.tsv \\')
    lines.append('  -t 0 -n 12')
    if task_id is not None:
        lines.append(f'_log "INFO" "Step {step_num}: DADA2 完成"')

    produced["FEATURE_SEQS"] = "featureSeqs.qza"
    produced["FEATURE_TABLE"] = "featureTable.biom"
    produced["FEATURE_FASTA"] = "feature.fasta"


def _build_single_command(call_def, produced: dict, extra: dict) -> str:
    """为通用工具构建单条 bash 命令。"""
    cmd_parts = [f"bash ${{AMPLICON_ROOT}}/{call_def.script_path}"]

    for param in call_def.params:
        dt = param.data_type

        if dt == "_CONFIG":
            if param.default:
                cmd_parts.append(f'{param.flag} {param.default}')
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
