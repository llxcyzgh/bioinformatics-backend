#!/bin/bash
# step3_genus_tree.sh - 属水平进化树脚本
# 用法：bash step3_genus_tree.sh -t <taxonomy> -g <genus_table> -r <relative_table> -a <asv_table> -s <feature.fasta> -o <output_dir> [-G <group_genus_table>]

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
SELECT_OTUS_PL="${SELECT_OTUS_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/select_OTUs.pl}"
MAKE_GENUS_TABLE_PL="${MAKE_GENUS_TABLE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/lib/make_genus_table.pl}"
DEL_PL="${DEL_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/lib/del.pl}"
CIRCLE_TREE_PL="${CIRCLE_TREE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/lib/circle_tree.pl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"
QIIME1_CONDA_BIN="${QIIME1_CONDA_BIN:-/gfs/users/guorongjun/miniconda3/bin}"
QIIME1_ENV="${QIIME1_ENV:-qiime1}"

# 筛选与建树 Top N（与 Step9.GenusTree.sh 一致）
SELECT_TOP_N="${SELECT_TOP_N:-10}"
TREE_TOP_N="${TREE_TOP_N:-100}"

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -x "${PERL_BIN}" ]; then
    echo "❌ 错误：PERL_BIN 不存在：${PERL_BIN}"
    exit 1
fi
for script in SELECT_OTUS_PL MAKE_GENUS_TABLE_PL DEL_PL CIRCLE_TREE_PL; do
    if [ ! -f "${!script}" ]; then
        echo "❌ 错误：${script} 不存在：${!script}"
        exit 1
    fi
done
if [ ! -f "${QIIME1_CONDA_BIN}/activate" ]; then
    echo "❌ 错误：QIIME1 activate 不存在：${QIIME1_CONDA_BIN}/activate"
    echo "   可通过环境变量覆盖，例如：export QIIME1_CONDA_BIN=\"/your/path/to/miniconda3/bin\""
    exit 1
fi

# 构建单套属进化树（样本或分组）
_build_genus_tree() {
    local work_dir="$1"
    local genus_table="$2"
    local tree_prefix="$3"
    local mat_draw_name="$4"
    local asv_table="$5"
    local feature_fasta="$6"
    local tree_top="$7"
    local label="$8"

    echo ""
    echo "🌳 ${label}..."
    mkdir -p "${work_dir}"
    (
        cd "${work_dir}"

        echo "  [1/6] 准备属序列 (make_genus_table.pl)..."
        "${PERL_BIN}" "${MAKE_GENUS_TABLE_PL}" \
            "${genus_table}" "${asv_table}" "${feature_fasta}" \
            preselected_genus.fasta phylum.list "${tree_top}"

        echo "  [2/6] 过滤序列 (del.pl)..."
        "${PERL_BIN}" "${DEL_PL}" preselected_genus.fasta > selected_genus.fasta

        echo "  [3/6] 多序列比对 (muscle)..."
        source "${QIIME1_CONDA_BIN}/activate" "${QIIME1_ENV}"
        align_seqs.py -i selected_genus.fasta -m muscle

        echo "  [4/6] 构建进化树..."
        make_phylogeny.py -i muscle_aligned/selected_genus_aligned.fasta -o "${tree_prefix}.tree"

        echo "  [5/6] 准备丰度矩阵并绘制环形树..."
        "${PERL_BIN}" -ne 'chomp (my @l = split /\t/); $l[0] =~ s/ /_/g; print join ("\t", @l[0..$#l-1]), "\n";' \
            "${genus_table}" | head -"$((tree_top + 1))" > "${mat_draw_name}"

        "${PERL_BIN}" "${CIRCLE_TREE_PL}" \
            --tree "${tree_prefix}.tree" \
            --group_list phylum.list \
            --species_abundance "${mat_draw_name}" \
            > "${tree_prefix}.tree.svg"

        echo "  [6/6] SVG → PDF/PNG..."
        if [ -x "${CONVERT_BIN}" ]; then
            "${CONVERT_BIN}" -density 200 "${tree_prefix}.tree.svg" "${tree_prefix}.tree.pdf"
            "${CONVERT_BIN}" -density 200 "${tree_prefix}.tree.svg" "${tree_prefix}.tree.png"
        else
            echo "  ⚠️  未找到 convert（CONVERT_BIN=${CONVERT_BIN}），跳过 PDF/PNG 转换"
        fi
    )
    echo "  ✅ ${label} 完成"
}

TAXONOMY=""
GENUS_TABLE=""
RELATIVE_TABLE=""
ASV_TABLE=""
ASV_SEQS=""
GROUP_GENUS_TABLE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--taxonomy) TAXONOMY="$2"; shift 2 ;;
        -g|--genus-table) GENUS_TABLE="$2"; shift 2 ;;
        -r|--relative-table) RELATIVE_TABLE="$2"; shift 2 ;;
        -a|--asv-table) ASV_TABLE="$2"; shift 2 ;;
        -s|--asv-seqs) ASV_SEQS="$2"; shift 2 ;;
        -G|--group-genus-table) GROUP_GENUS_TABLE="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_genus_tree.sh -t <taxonomy> -g <genus_table> -r <relative_table> -a <asv_table> -s <feature.fasta> -o <output> [-G <group_genus_table>]"
            echo ""
            echo "参数:"
            echo "  -t, --taxonomy         物种注释表 (all_tax_assignments.txt)"
            echo "  -g, --genus-table      属水平相对丰度表 (asv_table.g.relative.xls)"
            echo "  -r, --relative-table   样本相对丰度表 (asv_table.relative.xls，用于 select_OTUs)"
            echo "  -a, --asv-table        ASV 特征表 (asv_table.txt)"
            echo "  -s, --asv-seqs         ASV 代表序列 (feature.fasta)"
            echo "  -G, --group-genus-table  分组属水平相对丰度表 (可选，asv_table_group.g.relative.xls)"
            echo "  -o, --output           输出目录"
            echo "  -h, --help             显示帮助"
            echo ""
            echo "环境变量:"
            echo "  SELECT_TOP_N  select_OTUs 筛选 Top N（默认：10）"
            echo "  TREE_TOP_N    进化树 Top N 属（默认：100）"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${TAXONOMY}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${GENUS_TABLE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ -z "${RELATIVE_TABLE}" ] && { echo "❌ 错误：必须提供 -r"; exit 1; }
[ -z "${ASV_TABLE}" ] && { echo "❌ 错误：必须提供 -a"; exit 1; }
[ -z "${ASV_SEQS}" ] && { echo "❌ 错误：必须提供 -s"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

for f in TAXONOMY GENUS_TABLE RELATIVE_TABLE ASV_TABLE ASV_SEQS; do
    [ ! -f "${!f}" ] && { echo "❌ 错误：${f} 不存在：${!f}"; exit 1; }
done
if [ -n "${GROUP_GENUS_TABLE}" ] && [ ! -f "${GROUP_GENUS_TABLE}" ]; then
    echo "❌ 错误：分组属丰度表不存在：${GROUP_GENUS_TABLE}"
    exit 1
fi

# ----- 路径转绝对路径（cd 输出目录前） -----
TAXONOMY="$(abs_path_file "${TAXONOMY}")"
GENUS_TABLE="$(abs_path_file "${GENUS_TABLE}")"
RELATIVE_TABLE="$(abs_path_file "${RELATIVE_TABLE}")"
ASV_TABLE="$(abs_path_file "${ASV_TABLE}")"
ASV_SEQS="$(abs_path_file "${ASV_SEQS}")"
GROUP_GENUS_TABLE="$(abs_path_file_optional "${GROUP_GENUS_TABLE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "属水平进化树构建"
echo "=========================================="
echo ""
echo "📊 物种注释：${TAXONOMY}"
echo "📊 属丰度表：${GENUS_TABLE}"
echo "📊 样本相对丰度：${RELATIVE_TABLE}"
echo "📊 ASV 特征表：${ASV_TABLE}"
echo "📊 ASV 序列：${ASV_SEQS}"
if [ -n "${GROUP_GENUS_TABLE}" ]; then
    echo "📊 分组属丰度表：${GROUP_GENUS_TABLE}"
fi
echo ""

echo "🔬 [1/N] 筛选 Top 属及其 OTU/ASV (select_OTUs.pl)..."
"${PERL_BIN}" "${SELECT_OTUS_PL}" \
    "${TAXONOMY}" "${GENUS_TABLE}" \
    --sprefix g__ -full --top "${SELECT_TOP_N}" \
    --otutab "${RELATIVE_TABLE}" \
    --outdir selOTUs/

_build_genus_tree \
    "genus_evolutionary_tree" \
    "${GENUS_TABLE}" \
    "genus_${TREE_TOP_N}" \
    "asv_table.g.relative.mat.draw" \
    "${ASV_TABLE}" \
    "${ASV_SEQS}" \
    "${TREE_TOP_N}" \
    "样本属进化树 (Top ${TREE_TOP_N})"

if [ -n "${GROUP_GENUS_TABLE}" ]; then
    _build_genus_tree \
        "genus_evolutionary_tree_group" \
        "${GROUP_GENUS_TABLE}" \
        "genus_group_${TREE_TOP_N}" \
        "asv_table_group.g.relative.mat.draw" \
        "${ASV_TABLE}" \
        "${ASV_SEQS}" \
        "${TREE_TOP_N}" \
        "分组属进化树 (Top ${TREE_TOP_N})"
else
    echo ""
    echo "⚠️  未提供 -G 分组属丰度表，跳过分组属进化树"
fi

echo ""
echo "✅ 属水平进化树构建完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - selOTUs/: Top 属 OTU 筛选结果"
echo "   - genus_evolutionary_tree/genus_${TREE_TOP_N}.tree.{svg,pdf,png}: 样本属进化树"
if [ -n "${GROUP_GENUS_TABLE}" ]; then
    echo "   - genus_evolutionary_tree_group/genus_group_${TREE_TOP_N}.tree.{svg,pdf,png}: 分组属进化树"
fi
echo ""
