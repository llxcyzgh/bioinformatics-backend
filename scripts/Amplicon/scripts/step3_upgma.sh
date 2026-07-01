#!/bin/bash
# step3_upgma.sh - UPGMA 树构建脚本
# 用法：bash step3_upgma.sh -i <asv_table.even.txt> -t <tree.nwk> -m <alpha.mf> -o <output_dir> [-G <group_even.txt>] [--unweighted-pcoa ... --weighted-pcoa ...]

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
CONDA_BIN="${CONDA_BIN:-/software/anaconda3/bin}"
CONDA_ENV="${CONDA_ENV:-16s-env}"
QIIME1_CONDA_BIN="${QIIME1_CONDA_BIN:-/gfs/users/guorongjun/miniconda3/bin}"
QIIME1_ENV="${QIIME1_ENV:-qiime1}"
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
PCOA_PL="${PCOA_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/betaAnalysis/pcoa.pl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -f "${CONDA_BIN}/activate" ]; then
    echo "❌ 错误：CONDA activate 不存在：${CONDA_BIN}/activate"
    exit 1
fi
if [ ! -f "${QIIME1_CONDA_BIN}/activate" ]; then
    echo "❌ 错误：QIIME1 activate 不存在：${QIIME1_CONDA_BIN}/activate"
    exit 1
fi
if [ ! -f "${PCOA_PL}" ]; then
    echo "❌ 错误：PCOA_PL 不存在：${PCOA_PL}"
    exit 1
fi

# 确保元数据含 QIIME 表头 #SampleID	Description
_prepare_mapping() {
    local src="$1"
    local out_name="$2"
    local _first_line

    _first_line=$(head -1 "${src}" | tr -d '\r')
    if [[ "${_first_line}" == "#SampleID	Description" ]]; then
        echo "${src}"
        return 0
    fi

    local dst="${OUTPUT_DIR}/${out_name}"
    if [[ "${_first_line}" == "SampleID	Description" ]]; then
        echo "📝 ${out_name} 表头缺少 # 前缀，自动修正..." >&2
        {
            printf '#SampleID\tDescription\n'
            tail -n +2 "${src}"
        } > "${dst}"
    else
        echo "📝 ${out_name} 缺少表头 #SampleID	Description，自动补全..." >&2
        {
            printf '#SampleID\tDescription\n'
            cat "${src}"
        } > "${dst}"
    fi
    echo "   ✅ 已生成 ${dst}" >&2
    echo "${dst}"
}

# 由 alpha.mf 生成 group.mf（提取唯一分组名，两列均为组名）
_build_group_mf_from_meta() {
    local meta_file="$1"
    local dst="${OUTPUT_DIR}/group.mf"

    echo "📝 由 alpha.mf 生成 group.mf..." >&2
    {
        printf '#SampleID\tDescription\n'
        awk -F'\t' 'NR>1 && NF>=2 && $1 !~ /^#/ {groups[$2]=1} END {for (g in groups) print g "\t" g}' \
            "${meta_file}" | sort
    } > "${dst}"
    echo "   ✅ 已生成 ${dst}" >&2
    echo "${dst}"
}

# TSV/TXT → BIOM
_to_biom() {
    local input="$1"
    local output="$2"

    if [[ "${input}" == *.biom ]]; then
        echo "${input}"
        return 0
    fi

    source "${CONDA_BIN}/activate" "${CONDA_ENV}"
    biom convert \
        -i "${input}" \
        -o "${output}" \
        --to-json \
        --table-type="OTU table"
    echo "${output}"
}

# 从均一化表计算 seqs_per_sample（参考 Step8：首列样本 reads 总和）
_calc_seqs_per_sample() {
    local depth_table="$1"
    local depth

    depth=$(awk -F'\t' 'NR>1 && $2+0==$2 {sum += $2} END {print int(sum)}' "${depth_table}")
    if [ -z "${depth}" ] || [ "${depth}" -lt 1 ]; then
        echo "❌ 错误：无法从 ${depth_table} 计算 seqs_per_sample"
        exit 1
    fi
    echo "${depth}"
}

# 构建 UPGMA 树（样本或分组）
_build_upgma() {
    local biom_table="$1"
    local mapping_file="$2"
    local tree_file="$3"
    local upgma_dir="$4"
    local biom_basename="$5"
    local dm_tag="$6"
    local weighted_support_mode="$7"
    local label="$8"

    echo ""
    echo "🌳 ${label}..."
    source "${QIIME1_CONDA_BIN}/activate" "${QIIME1_ENV}"

    echo "  [1/4] jackknifed_beta_diversity.py..."
    jackknifed_beta_diversity.py \
        --otu_table_fp "${biom_table}" \
        --force \
        --mapping_fp "${mapping_file}" \
        --tree_fp "${tree_file}" \
        --output_dir "${upgma_dir}" \
        --seqs_per_sample "${SEQS_PER_SAMPLE}"

    mkdir -p "${upgma_dir}/unweighted_unifrac" "${upgma_dir}/weighted_unifrac"

    echo "  [2/4] Unweighted UniFrac 树 (make_bootstrapped_tree.py)..."
    make_bootstrapped_tree.py \
        --master_tree "${upgma_dir}/unrarefied_bdiv/${biom_basename}_unweighted_unifrac_upgma.tre" \
        --support "${upgma_dir}/unweighted_unifrac/upgma_cmp/jackknife_support.txt" \
        --output_file "${upgma_dir}/unweighted_unifrac/unweighted_unifrac.pdf"

    if [ -x "${CONVERT_BIN}" ]; then
        "${CONVERT_BIN}" \
            "${upgma_dir}/unweighted_unifrac/unweighted_unifrac.pdf" \
            "${upgma_dir}/unweighted_unifrac/unweighted_unifrac.png"
    else
        echo "  ⚠️  未找到 convert，跳过 unweighted PNG"
    fi

    local weighted_support="${upgma_dir}/unweighted_unifrac/upgma_cmp/jackknife_support.txt"
    if [ "${weighted_support_mode}" = "weighted" ]; then
        weighted_support="${upgma_dir}/weighted_unifrac/upgma_cmp/jackknife_support.txt"
    fi

    echo "  [3/4] Weighted UniFrac 树 (make_bootstrapped_tree.py)..."
    make_bootstrapped_tree.py \
        --master_tree "${upgma_dir}/unrarefied_bdiv/${biom_basename}_weighted_unifrac_upgma.tre" \
        --support "${weighted_support}" \
        --output_file "${upgma_dir}/weighted_unifrac/weighted_unifrac.pdf"

    if [ -x "${CONVERT_BIN}" ]; then
        "${CONVERT_BIN}" \
            "${upgma_dir}/weighted_unifrac/weighted_unifrac.pdf" \
            "${upgma_dir}/weighted_unifrac/weighted_unifrac.png"
    else
        echo "  ⚠️  未找到 convert，跳过 weighted PNG"
    fi

    echo "  [4/4] 整理距离矩阵..."
    mv -f "${upgma_dir}/unrarefied_bdiv/unweighted_unifrac_${biom_basename}.txt" \
        "PCoA_data/unweighted_unifrac${dm_tag}_dm.txt"
    mv -f "${upgma_dir}/unrarefied_bdiv/weighted_unifrac_${biom_basename}.txt" \
        "PCoA_data/weighted_unifrac${dm_tag}_dm.txt"

    echo "  ✅ ${label} 完成"
}

EVEN_TABLE=""
DEPTH_TABLE=""
TREE_FILE=""
META_FILE=""
GROUP_TABLE=""
UNWEIGHTED_PCOA=""
WEIGHTED_PCOA=""
OUTPUT_DIR=""
SEQS_PER_SAMPLE="${SEQS_PER_SAMPLE:-}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) EVEN_TABLE="$2"; shift 2 ;;
        -t|--tree) TREE_FILE="$2"; shift 2 ;;
        -m|--meta) META_FILE="$2"; shift 2 ;;
        -G|--group-input) GROUP_TABLE="$2"; shift 2 ;;
        --unweighted-pcoa) UNWEIGHTED_PCOA="$2"; shift 2 ;;
        --weighted-pcoa) WEIGHTED_PCOA="$2"; shift 2 ;;
        -d|--depth-table) DEPTH_TABLE="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_upgma.sh -i <asv_table.even.txt> -t <tree.nwk> -m <alpha.mf> -o <output> [选项]"
            echo ""
            echo "参数:"
            echo "  -i, --input            均一化 ASV 表（TSV/TXT 或 BIOM）"
            echo "  -t, --tree             有根系统发育树 (tree.nwk)"
            echo "  -m, --meta             样本元数据 (alpha.mf)"
            echo "  -G, --group-input      分组均一化表 asv_table.group.even.txt（可选，group.mf 由 -m 自动生成）"
            echo "  --unweighted-pcoa      非加权 UniFrac PCoA ordination.txt（可选，来自 step3_beta_data）"
            echo "  --weighted-pcoa        加权 UniFrac PCoA ordination.txt（可选，来自 step3_beta_data）"
            echo "  -d, --depth-table      用于计算 seqs_per_sample 的 TSV（输入为 BIOM 时使用）"
            echo "  -o, --output           输出目录"
            echo "  -h, --help             显示帮助"
            echo ""
            echo "环境变量:"
            echo "  SEQS_PER_SAMPLE  手动指定采样深度（默认从均一化表自动计算）"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${EVEN_TABLE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${TREE_FILE}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${META_FILE}" ] && { echo "❌ 错误：必须提供 -m"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
[ ! -f "${EVEN_TABLE}" ] && { echo "❌ 错误：输入表不存在：${EVEN_TABLE}"; exit 1; }
[ ! -f "${TREE_FILE}" ] && { echo "❌ 错误：进化树不存在：${TREE_FILE}"; exit 1; }
[ ! -f "${META_FILE}" ] && { echo "❌ 错误：元数据不存在：${META_FILE}"; exit 1; }

# ----- 路径转绝对路径（cd 输出目录前） -----
EVEN_TABLE="$(abs_path_file "${EVEN_TABLE}")"
DEPTH_TABLE="$(abs_path_file_optional "${DEPTH_TABLE}")"
TREE_FILE="$(abs_path_file "${TREE_FILE}")"
META_FILE="$(abs_path_file "${META_FILE}")"
GROUP_TABLE="$(abs_path_file_optional "${GROUP_TABLE}")"
UNWEIGHTED_PCOA="$(abs_path_file_optional "${UNWEIGHTED_PCOA}")"
WEIGHTED_PCOA="$(abs_path_file_optional "${WEIGHTED_PCOA}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"/{UPGMA_sample,UPGMA_group,PCoA_data}
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "UPGMA 树构建"
echo "=========================================="
echo ""

# 元数据表头校验；分组 UPGMA 时由 alpha.mf 自动生成 group.mf
META_FILE_QIIME=$(_prepare_mapping "${META_FILE}" "alpha.qiime.mf")
if [ -n "${GROUP_TABLE}" ]; then
    GROUP_META_QIIME=$(_build_group_mf_from_meta "${META_FILE_QIIME}")
fi

# 深度计算用 TSV
if [ -z "${DEPTH_TABLE}" ]; then
    if [[ "${EVEN_TABLE}" == *.txt ]] || [[ "${EVEN_TABLE}" == *.tsv ]]; then
        DEPTH_TABLE="${EVEN_TABLE}"
    elif [ -n "${SEQS_PER_SAMPLE}" ]; then
        DEPTH_TABLE=""
    else
        echo "❌ 错误：输入为 BIOM 时请提供 -d <depth_table.txt> 或设置 SEQS_PER_SAMPLE"
        exit 1
    fi
fi

if [ -z "${SEQS_PER_SAMPLE}" ]; then
    SEQS_PER_SAMPLE="$(_calc_seqs_per_sample "${DEPTH_TABLE}")"
fi
echo "📊 seqs_per_sample：${SEQS_PER_SAMPLE}"

# 转换为 BIOM
echo "📥 准备 BIOM 表..."
SAMPLE_BIOM_LOCAL="asv_table.even.biom"
SAMPLE_BIOM="$(_to_biom "${EVEN_TABLE}" "${SAMPLE_BIOM_LOCAL}")"
SAMPLE_BIOM_BASE="$(basename "${SAMPLE_BIOM}" .biom)"

if [ -n "${GROUP_TABLE}" ]; then
    GROUP_BIOM_LOCAL="asv_table.group.even.biom"
    GROUP_BIOM="$(_to_biom "${GROUP_TABLE}" "${GROUP_BIOM_LOCAL}")"
    GROUP_BIOM_BASE="$(basename "${GROUP_BIOM}" .biom)"
fi

echo "📊 样本表：${EVEN_TABLE}"
echo "📊 进化树：${TREE_FILE}"
echo "📊 样本元数据：${META_FILE_QIIME}"
if [ -n "${GROUP_TABLE}" ]; then
    echo "📊 分组表：${GROUP_TABLE}"
    echo "📊 分组元数据：${GROUP_META_QIIME}（由 alpha.mf 生成）"
fi
echo ""

_build_upgma \
    "${SAMPLE_BIOM}" \
    "${META_FILE_QIIME}" \
    "${TREE_FILE}" \
    "UPGMA_sample" \
    "${SAMPLE_BIOM_BASE}" \
    "" \
    "unweighted" \
    "样本 UPGMA 树"

if [ -n "${UNWEIGHTED_PCOA}" ] && [ -f "${UNWEIGHTED_PCOA}" ]; then
    echo ""
    echo "📊 导出非加权 UniFrac PCoA 坐标..."
    "${PERL_BIN}" "${PCOA_PL}" \
        "${UNWEIGHTED_PCOA}" \
        "PCoA_data/unweighted_unifrac_pc.txt"
fi
if [ -n "${WEIGHTED_PCOA}" ] && [ -f "${WEIGHTED_PCOA}" ]; then
    echo "📊 导出加权 UniFrac PCoA 坐标..."
    "${PERL_BIN}" "${PCOA_PL}" \
        "${WEIGHTED_PCOA}" \
        "PCoA_data/weighted_unifrac_pc.txt"
fi

if [ -n "${GROUP_TABLE}" ]; then
    _build_upgma \
        "${GROUP_BIOM}" \
        "${GROUP_META_QIIME}" \
        "${TREE_FILE}" \
        "UPGMA_group" \
        "${GROUP_BIOM_BASE}" \
        "_group" \
        "weighted" \
        "分组 UPGMA 树"
else
    echo ""
    echo "⚠️  未提供 -G 分组均一化表，跳过分组 UPGMA 树"
fi

echo ""
echo "✅ UPGMA 树构建完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - UPGMA_sample/unrarefied_bdiv/${SAMPLE_BIOM_BASE}_unweighted_unifrac_upgma.tre"
echo "   - UPGMA_sample/unrarefied_bdiv/${SAMPLE_BIOM_BASE}_weighted_unifrac_upgma.tre"
echo "   - UPGMA_sample/unweighted_unifrac/unweighted_unifrac.png"
echo "   - UPGMA_sample/weighted_unifrac/weighted_unifrac.png"
echo "   - PCoA_data/unweighted_unifrac_dm.txt"
echo "   - PCoA_data/weighted_unifrac_dm.txt"
if [ -n "${GROUP_TABLE}" ]; then
    echo "   - UPGMA_group/unrarefied_bdiv/${GROUP_BIOM_BASE}_unweighted_unifrac_upgma.tre"
    echo "   - UPGMA_group/unrarefied_bdiv/${GROUP_BIOM_BASE}_weighted_unifrac_upgma.tre"
    echo "   - UPGMA_group/unweighted_unifrac/unweighted_unifrac.png"
    echo "   - UPGMA_group/weighted_unifrac/weighted_unifrac.png"
    echo "   - PCoA_data/unweighted_unifrac_group_dm.txt"
    echo "   - PCoA_data/weighted_unifrac_group_dm.txt"
fi
if [ -f "PCoA_data/unweighted_unifrac_pc.txt" ]; then
    echo "   - PCoA_data/unweighted_unifrac_pc.txt"
    echo "   - PCoA_data/weighted_unifrac_pc.txt"
fi
echo ""
