"""
编排脚本生成器：根据工具链生成 bash 编排脚本。
每个步骤调用独立的 sh 脚本，通过参数传递 input/output 文件。

v2 契约：每个脚本都强制 `-o <Tool>_Output/`（输出目录）。产物写进该目录，
本生成器据此
  • 给每步发 `-o "<Tool>_Output"`；
  • 把产物注册成 `<Tool>_Output>/<file>`，使下一步 -i 准确指向上一步的输出目录。
per-sample 区与 manifest（DADA2）步骤也已通用化：不再按字面 tool_id 分发，
而是按 ScriptCallDef 的 data_type / _MANIFEST 标记驱动。
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


def _output_dir_default(call_def: ScriptCallDef) -> str:
    """该工具 `-o _OUTPUT_DIR` ParamDef 的默认目录名（如 "DADA2_Output"）；没有则空串。"""
    for p in call_def.params:
        if p.data_type == "_OUTPUT_DIR":
            return p.default or ""
    return ""


# 根 FASTQ 输入：data_type → 关联数组名。_gen_parallel_region 据 samples 的上传哈希
# 发 `declare -A R1_OF R2_OF` + 每样本 `/shared/<hash>`，循环内用 ${R1_OF[$SAMPLE]} 取。
_ROOT_INPUT_ARRAY = {
    "FASTQ_R1": "R1_OF",
    "FASTQ_R2": "R2_OF",
}

# glob 兜底模式：data_type → (glob, fallback)。仅当无样本映射（samples 为空）时用，
# 保留"按样本名找文件"的稳健性。
_ROOT_INPUT_GLOBS = {
    "FASTQ_R1": ("/shared/${SAMPLE}*.R1*", "/shared/${SAMPLE}.R1.fastq.gz"),
    "FASTQ_R2": ("/shared/${SAMPLE}*.R2*", "/shared/${SAMPLE}.R2.fastq.gz"),
}

# vs.list / rf.list 消费者 → (生成文件名, 配对格式)。这类「组间对比配对」清单无节点产出，
# 由头部从 group.list 的组别两两配对自动生成（2 组→1 对，N 组→全配对 C(N,2)）。
# 格式由各脚本解析逻辑决定：lefse 用 A_vs_B（step4_lefse.md），metastat/randomforest 用 A<TAB>B。
_LIST_PAIR_CONSUMERS = {
    "amp-lefse":        ("lefse_vs.list", "vs"),
    "amp-metastat":     ("Vs.list",        "tab"),
    "amp-randomforest": ("rf.list",        "tab"),
}

# 头部生成 vs.list/rf.list 的 awk 片段：从 group.list 第2列取组别 → sort -u → 两两配对。
# \t/\n 保持字面（awk 的 printf 在格式串里解释为 tab/换行）。
_AWK_DISTINCT_GROUPS = r"awk 'NF>=2 && $1!~/^#/{print $2}' group.list | sort -u"
_AWK_PAIRS_TAB = r"""awk '{g[++n]=$1} END{for(i=1;i<=n;i++)for(j=i+1;j<=n;j++)printf "%s\t%s\n",g[i],g[j]}'"""
_AWK_PAIRS_VS = r"""awk '{g[++n]=$1} END{for(i=1;i<=n;i++)for(j=i+1;j<=n;j++)printf "%s_vs_%s\n",g[i],g[j]}'"""


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

    # 链路中是否有消费 group.list 的工具（-g _GROUP_LIST）。
    # 是则尝试从 metadata 自动派生 group.list（见头部生成处）。
    needs_group_list = any(
        cd and any(p.data_type == "_GROUP_LIST" for p in cd.params)
        for cd in (call_defs.get(tid) for tid in tool_ids)
    )

    # 链路中消费 vs.list/rf.list 的工具（组间对比配对），按 _LIST_PAIR_CONSUMERS 表。
    list_consumers = [tid for tid in tool_ids if tid in _LIST_PAIR_CONSUMERS]

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
        if type_id == "FASTQ_PAIR":
            # FASTQ 对在 per-sample 循环里经关联数组 R1_OF/R2_OF 引用；
            # 头部不发（避免只列首个样本、与多样本实际情况不符的误导）。
            continue
        if type_id == "METADATA":
            # METADATA 由下方 metadata_stored 块统一发（同时驱动 group.list 派生），
            # 避免这里再发一次造成 METADATA= 重复。
            continue
        path = uploaded_files.get(type_id, "")
        if path:
            var_name = type_id.replace("-", "_")
            lines.append(f'{var_name}="{path}"')
    if metadata_stored:
        lines.append(f'METADATA="/shared/{metadata_stored}"')
    # group.list：链路需要分组（-g _GROUP_LIST）时，从 metadata 自动抽取
    # 「样本名 + 分组(Description)」两列生成。metadata 格式由 beta-data 约定
    # （#SampleID<TAB/逗号>Description，第1列样本、第2列分组），故第2列即分组列。
    # 未上传 metadata 时无法派生 → 分组类步骤将失败（已知限制，不静默伪造）。
    if needs_group_list or list_consumers:
        # group.list：被 -g _GROUP_LIST 消费，也是 vs.list/rf.list 派生的输入。
        if metadata_stored:
            lines.append('awk -F\'[\\t,]\' \'/^#/{next} NF>=2{print $1"\\t"$2}\' "$METADATA" > group.list')
        else:
            lines.append("# ⚠ 链路需要 group.list（分组信息）但未上传 metadata；分组类步骤将失败")
    # vs.list / rf.list：组间对比配对清单，从 group.list 的组别两两配对自动生成
    # （无节点产出，类同 group.list）。未上传 metadata 时无法生成 → 相关步骤失败。
    if list_consumers:
        if metadata_stored:
            lines.append("# ─── vs.list / rf.list：从 group.list 的组别两两配对自动生成 ───")
            lines.append("# 2 组→1 对；N 组→全部 C(N,2) 对。lefse=A_vs_B；metastat/randomforest=A<TAB>B。")
            for tid in tool_ids:
                spec = _LIST_PAIR_CONSUMERS.get(tid)
                if not spec:
                    continue
                fname, fmt = spec
                pairs_awk = _AWK_PAIRS_VS if fmt == "vs" else _AWK_PAIRS_TAB
                lines.append(f"{_AWK_DISTINCT_GROUPS} | {pairs_awk} > {fname}")
        else:
            lines.append("# ⚠ 链路需要 vs.list/rf.list（组间对比配对）但未上传 metadata；相关步骤将失败")
    lines.append("")

    # ─── 跟踪已生成的文件 ───
    produced_files: dict[str, str] = {}  # data_type → file path（含输出目录前缀）
    # 初始化用户上传的根输入
    for rf in required_files:
        type_id = rf.get("typeId", "")
        if type_id != "FASTQ_PAIR" and type_id in uploaded_files:
            produced_files[type_id] = uploaded_files[type_id]

    step_num = 0
    total_steps = len(tool_ids)
    last_region_outputs: dict[str, str] | None = None  # per-sample 区产物模板，供 manifest 用

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
            step_num, last_region_outputs = _gen_parallel_region(
                lines, region, call_defs, tool_names, samples, extra,
                step_num, total_steps, task_id, param_overrides,
            )
            continue

        # ─── 非 per-sample（dada2/manifest / 通用）: 单次执行，在并行区 wait 之后 ───
        step_num += 1
        tool_overrides = (param_overrides or {}).get(tool_id, {})
        _emit_step_header(lines, step_num, total_steps, tool_name, task_id)
        is_manifest = any(p.data_type == "_MANIFEST" for p in call_def.params)
        if is_manifest:
            # DADA2 等 manifest 步骤：先生成 manifest（吃 per-sample 区的 QC 产物）再调用
            _gen_manifest_step(
                lines, call_def, samples, last_region_outputs,
                produced_files, extra, step_num, task_id, tool_overrides, tool_name,
            )
        else:
            if task_id is not None:
                lines.append(f'_log "INFO" "Step {step_num}/{total_steps}: {tool_name} 执行中"')
            lines.append(_build_single_command(call_def, produced_files, extra, tool_overrides))
        # 注册产物（带输出目录前缀，使下游 -i 指向 <Tool>_Output/<file>）
        out_dir = _output_dir_default(call_def)
        for out in call_def.outputs:
            fname = out.filename
            produced_files[out.data_type] = f"{out_dir}/{fname}" if out_dir else fname
        last_region_outputs = None  # manifest 已消费，清空
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


def _emit_call(lines: list[str], script_path: str, args: list[str], indent: str = "  ") -> None:
    """输出 `bash <path> arg1 ... `，反斜杠续行（首行 indent 缩进，续行再多 2 空格）。"""
    cont = indent + "  "
    if not args:
        lines.append(f'{indent}bash ${{AMPLICON_ROOT}}/{script_path}')
        return
    lines.append(f'{indent}bash ${{AMPLICON_ROOT}}/{script_path} \\')
    last = len(args) - 1
    for i, a in enumerate(args):
        sep = " \\" if i < last else ""
        lines.append(f'{cont}{a}{sep}')


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
                         samples: dict, extra: dict,
                         step_num: int, total_steps: int, task_id, param_overrides) -> tuple[int, dict[str, str]]:
    """把连续的 per-sample 工具合并成一个跨样本并行区。

    每个样本在后台子shell内按序跑完整条链（文件名依赖决定顺序），跨样本并行；
    显式 wait 屏障后再由调用方跑 manifest 等汇合步骤。
    返回 (新的 step_num, 该区最终产物模板 dict)。
    """
    start = step_num + 1
    end = step_num + len(region_ids)
    label = " → ".join(tool_names.get(t, t) for t in region_ids)
    lines.append(f"# ─── Step {start}-{end}/{total_steps}: {label}（per-sample 并行） ───")
    if task_id is not None:
        lines.append(f'_log "INFO" "Steps {start}-{end}/{total_steps}: 并行预处理开始"')
    else:
        lines.append(f'echo "[$(date \'+%Y-%m-%d %H:%M:%S\')] [Steps {start}-{end}/{total_steps}] 并行预处理..."')

    # 样本→上传哈希路径关联数组：每样本 R1/R2 的真实 /shared/<hash>。
    # 循环内 ${R1_OF[$SAMPLE]} 直接取到，不再靠按样本名 glob（上传是哈希名，glob 找不到）。
    r1_entries = [(s, v["R1"]) for s, v in samples.items() if "R1" in v]
    r2_entries = [(s, v["R2"]) for s, v in samples.items() if "R2" in v]
    decl = []
    if r1_entries:
        decl.append("R1_OF")
    if r2_entries:
        decl.append("R2_OF")
    if decl:
        lines.append("declare -A {}".format(" ".join(decl)))
        for sname, stored in r1_entries:
            lines.append(f'R1_OF["{sname}"]="/shared/{stored}"')
        for sname, stored in r2_entries:
            lines.append(f'R2_OF["{sname}"]="/shared/{stored}"')

    lines.append("SAMPLES=({})".format(" ".join(f'"{s}"' for s in samples.keys())))
    lines.append('MAX_JOBS="${BIOFLOW_MAX_PARALLEL:-4}"')
    lines.append('if [ "$MAX_JOBS" -lt 1 ] 2>/dev/null; then MAX_JOBS=1; fi')
    lines.append("_JOB_I=0")
    lines.append('for SAMPLE in "${SAMPLES[@]}"; do')
    lines.append("  (")
    # 区内产物模板：data_type → "${sample}/..." 模板（首工具的根输入走 _ROOT_INPUT_GLOBS）
    produced_sample: dict[str, str] = {}
    for idx, tid in enumerate(region_ids):
        cd = call_defs.get(tid)
        if not cd:
            lines.append(f"    # ⚠ 未找到 {tid} 的脚本注册，跳过")
            continue
        ov = (param_overrides or {}).get(tid, {})
        s = step_num + idx + 1
        _gen_per_sample_body(
            lines, cd, produced_sample, tool_names.get(tid, tid), ov, extra, s, task_id, indent="    "
        )
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
    return end, produced_sample


def _gen_per_sample_body(lines, call_def: ScriptCallDef, produced_sample: dict[str, str],
                         tool_name: str, tool_overrides: dict, extra: dict,
                         step_num: int, task_id, indent: str = "") -> None:
    """单个样本的通用调用片段（不含 for/done/SAMPLES，供并行区子shell调用）。

    按 ScriptCallDef 解析参数：
      • `_OUTPUT_DIR` → `-o "<Tool>_Output"`；
      • `_CONFIG` → override 优先，否则 default；
      • `_PRIMER_F/_PRIMER_R` → 来自 extra；
      • 其它 `_*` → default 或跳过；
      • 普通数据类型 → 从 produced_sample 取模板，${sample}→${SAMPLE}；
      • 根 FASTQ 输入（FASTQ_R1/R2）→ glob 兜底（保留稳健性）。
    调用后把本工具 outputs 注册进 produced_sample（带输出目录前缀）。
    """
    out_dir = _output_dir_default(call_def)
    args: list[str] = []
    pre: list[str] = []  # shell 兜底变量定义（glob 等），需在调用前输出
    for param in call_def.params:
        dt = param.data_type
        if dt == "_OUTPUT_DIR":
            if out_dir:
                args.append(f'{param.flag} "{out_dir}"')
            continue
        if dt == "_CONFIG":
            value = tool_overrides.get(param.flag, param.default)
            if value:
                args.append(f"{param.flag} {value}")
            continue
        if dt == "_PRIMER_F":
            primer_f = extra.get("primer_f", COMMON_PRIMERS["16S V3-V4"]["f"])
            args.append(f'{param.flag} "{primer_f}"')
            continue
        if dt == "_PRIMER_R":
            primer_r = extra.get("primer_r", COMMON_PRIMERS["16S V3-V4"]["r"])
            args.append(f'{param.flag} "{primer_r}"')
            continue
        if dt.startswith("_"):
            # _MANIFEST/_METADATA/_GROUP_LIST 等在 per-sample 步骤里通常不出现；有 default 就发
            if param.default:
                args.append(f"{param.flag} {param.default}")
            continue
        # 普通数据类型 → 区内产物模板
        if dt in produced_sample:
            tmpl = produced_sample[dt].replace("${sample}", "${SAMPLE}")
            args.append(f'{param.flag} "{tmpl}"')
        elif dt in _ROOT_INPUT_ARRAY:
            # 根 FASTQ：从并行区发的关联数组取每样本实际上传哈希路径
            arr = _ROOT_INPUT_ARRAY[dt]
            args.append(f'{param.flag} "${{{arr}[$SAMPLE]}}"')
        elif dt in _ROOT_INPUT_GLOBS:
            # 兜底：无样本映射（samples 为空）时按样本名 glob
            glob_pat, fallback = _ROOT_INPUT_GLOBS[dt]
            var = f"{dt}_FILE"  # FASTQ_R1_FILE
            pre.append(f'{indent}{var}="{fallback}"')
            pre.append(f'{indent}for f in {glob_pat}; do {var}="$f"; break; done')
            args.append(f'{param.flag} "${{{var}}}"')
        elif param.required:
            args.append(f'{param.flag} "<{dt}>"')
        # optional 且无来源 → 跳过
    if task_id is not None:
        pre.append(f'{indent}_log "INFO" "Step {step_num}: {tool_name} ${{SAMPLE}}"')
    lines.extend(pre)
    _emit_call(lines, call_def.script_path, args, indent=indent or "  ")
    # 注册产物到 produced_sample（带输出目录前缀，模板保留 ${sample}）
    for out in call_def.outputs:
        produced_sample[out.data_type] = f"{out_dir}/{out.filename}" if out_dir else out.filename


def _gen_manifest_step(
    lines: list[str], call_def: ScriptCallDef, samples: dict,
    last_region_outputs: dict[str, str] | None, produced: dict, extra: dict,
    step_num: int, task_id, tool_overrides: dict, tool_name: str,
) -> None:
    """manifest 步骤（如 DADA2）：按 per-sample 区的 QC 产物生成 manifest.tsv，再调用工具。

    QC 文件模板取自 last_region_outputs["FASTQ_QC"]（形如 "Frags_QC_Output/${sample}.fastq"），
    逐样本把 ${sample} 替换成样本名。工具命令本身复用 _build_single_command（已带 -o <Tool>_Output）。
    """
    lines.append("# 生成 manifest 文件")
    lines.append('echo -e "sample-id\\tabsolute-filepath" > manifest.tsv')
    qc_tmpl = (last_region_outputs or {}).get("FASTQ_QC", "${sample}.fastq")
    if samples:
        for sample_name in samples:
            qc_file = qc_tmpl.replace("${sample}", sample_name)
            lines.append(f'echo -e "{sample_name}\\t$(pwd)/{qc_file}" >> manifest.tsv')
    else:
        lines.append("# ⚠ 未检测到样本，需手动编辑 manifest.tsv")
    lines.append("")
    if task_id is not None:
        lines.append(f'_log "INFO" "Step {step_num}: {tool_name} 开始"')
    lines.append(_build_single_command(call_def, produced, extra, tool_overrides))
    if task_id is not None:
        lines.append(f'_log "INFO" "Step {step_num}: {tool_name} 完成"')


def _build_single_command(call_def, produced: dict, extra: dict, tool_overrides: dict | None = None) -> str:
    """为通用工具构建单条 bash 命令（含 -o <Tool>_Output）。"""
    tool_overrides = tool_overrides or {}
    cmd_parts = [f"bash ${{AMPLICON_ROOT}}/{call_def.script_path}"]

    for param in call_def.params:
        dt = param.data_type

        if dt == "_OUTPUT_DIR":
            out_dir = param.default or ""
            if out_dir:
                cmd_parts.append(f'{param.flag} "{out_dir}"')
            continue

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
            # metadata_stored 是 confirm_upload 传入的裸哈希名，需补 /shared/ 前缀；
            # produced["_METADATA"]（若已注入）则已带前缀。
            meta = produced.get("_METADATA")
            if not meta:
                ms = extra.get("metadata_stored", "")
                meta = f"/shared/{ms}" if ms else ""
            if meta:
                cmd_parts.append(f'{param.flag} "{meta}"')
            continue

        if dt == "_GROUP_LIST":
            # group.list 通常由 metadata 生成
            cmd_parts.append(f'{param.flag} group.list')
            continue

        if dt in ("_VS_LIST", "_RF_LIST"):
            # vs.list/rf.list 由头部从 group.list 两两配对生成；文件名按工具约定
            spec = _LIST_PAIR_CONSUMERS.get(call_def.tool_id)
            if spec:
                cmd_parts.append(f"{param.flag} {spec[0]}")
            continue

        if dt.startswith("_"):
            # 其他特殊类型跳过
            if param.default:
                cmd_parts.append(f'{param.flag} {param.default}')
            continue

        # 普通数据类型 → 从 produced_files 中查找（已带 <Tool>_Output/ 前缀）
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
