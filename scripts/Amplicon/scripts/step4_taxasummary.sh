#!/bin/bash
# step4_taxasummary.sh - 物种组成热图脚本（样本水平）
# 用法：bash step4_taxasummary.sh -i <Relative/|asv_table.even.txt> -g <group.list> [-l <levels>] [--top <N>] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python}"
HEATMAP_DATA_PY="${HEATMAP_DATA_PY:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/heatmapData.py}"
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
HEATMAP_PLOT_R="${HEATMAP_PLOT_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/heatmapPlot.R}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

declare -A LEVEL_TO_CODE=(
    ["phylum"]="p"
    ["class"]="c"
    ["order"]="o"
    ["family"]="f"
    ["genus"]="g"
    ["species"]="s"
)
declare -A CODE_TO_NAME=(
    ["p"]="phylum"
    ["c"]="class"
    ["o"]="order"
    ["f"]="family"
    ["g"]="genus"
    ["s"]="species"
)
ALL_LEVELS=(phylum class order family genus species)

_parse_levels() {
    local input="$1"
    local token level
    declare -A seen=()
    SELECTED_LEVELS=()

    if [ -z "${input}" ]; then
        SELECTED_LEVELS=("${ALL_LEVELS[@]}")
        return 0
    fi

    local IFS=','
    for token in ${input}; do
        token="$(echo "${token}" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -z "${token}" ] && continue
        case "${token}" in
            phylum|p) level="phylum" ;;
            class|c) level="class" ;;
            order|o) level="order" ;;
            family|f) level="family" ;;
            genus|g) level="genus" ;;
            species|s) level="species" ;;
            *)
                echo "❌ 错误：未知分类层级：${token}"
                echo "   可选：phylum(p), class(c), order(o), family(f), genus(g), species(s)"
                exit 1
                ;;
        esac
        if [ -z "${seen[$level]}" ]; then
            seen[$level]=1
            SELECTED_LEVELS+=("${level}")
        fi
    done

    if [ "${#SELECTED_LEVELS[@]}" -eq 0 ]; then
        echo "❌ 错误：-l 未指定有效分类层级"
        exit 1
    fi
}

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

for bin in PERL_BIN PYTHON_BIN RSCRIPT_BIN CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        exit 1
    fi
done
for tool in STAT_OTU_TAB_PL HEATMAP_DATA_PY HEATMAP_PLOT_R; do
    if [ ! -f "${!tool}" ]; then
        echo "❌ 错误：${tool} 不存在：${!tool}"
        exit 1
    fi
done

INPUT_PATH=""
GROUP_FILE=""
LEVELS_ARG=""
SELECTED_LEVELS=()
TOP_N="35"
OUTPUT_DIR=""
GENERATED_RELATIVE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_PATH="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -l|--levels) LEVELS_ARG="$2"; shift 2 ;;
        --top) TOP_N="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step4_taxasummary.sh -i <Relative/|asv_table.even.txt> -g <group.list> [-l <levels>] [--top <N>] -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -i, --input      Relative/ 目录，或 step3 输出的 asv_table.even.txt"
            echo "  -g, --group      样本分组文件路径"
            echo "  -l, --levels     分析层级，逗号分隔（默认全部）"
            echo "  --top            Top 物种数量（默认：35）"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            echo ""
            echo "层级可选：phylum(p), class(c), order(o), family(f), genus(g), species(s)"
            echo "示例：-l phylum,genus  或  -l p,g"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

if [ -z "${INPUT_PATH}" ]; then echo "❌ 错误：必须提供 -i"; exit 1; fi
if [ -z "${GROUP_FILE}" ]; then echo "❌ 错误：必须提供 -g"; exit 1; fi
if [ ! -f "${GROUP_FILE}" ]; then echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; fi
if [ -z "${OUTPUT_DIR}" ]; then echo "❌ 错误：必须提供 -o"; exit 1; fi
if [ ! -f "${INPUT_PATH}" ] && [ ! -d "${INPUT_PATH}" ]; then
    echo "❌ 错误：输入路径不存在：${INPUT_PATH}"
    echo "   -i 可传 Relative/ 目录或 asv_table.even.txt 文件"
    exit 1
fi

_parse_levels "${LEVELS_ARG}"

GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"

if [ -f "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_file "${INPUT_PATH}")"
elif [ -d "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_dir "${INPUT_PATH}")"
else
    echo "❌ 错误：无法识别输入：${INPUT_PATH}"
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

if [ -f "${INPUT_PATH}" ]; then
    EVEN_TABLE="${INPUT_PATH}"
    RELATIVE_DIR="${OUTPUT_DIR}/Relative"
    echo ""
    echo "=========================================="
    echo "物种组成热图（样本水平）"
    echo "=========================================="
    echo ""
    echo "📊 均一化 ASV 表：${EVEN_TABLE}"
    echo "[0/N] 生成 Relative 相对丰度表..."
    mkdir -p "${RELATIVE_DIR}"
    "${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
        "${EVEN_TABLE}" \
        --prefix "${RELATIVE_DIR}/asv_table"
    echo "  ✅ Relative 目录：${RELATIVE_DIR}"
    GENERATED_RELATIVE=1
elif [ -d "${INPUT_PATH}" ]; then
    RELATIVE_DIR="${INPUT_PATH}"
else
    echo "❌ 错误：无法识别输入：${INPUT_PATH}"
    exit 1
fi

if [ ! -d "${RELATIVE_DIR}" ]; then
    echo "❌ 错误：相对丰度表目录不存在：${RELATIVE_DIR}"
    exit 1
fi

if [ "${GENERATED_RELATIVE}" -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "物种组成热图（样本水平）"
    echo "=========================================="
    echo ""
fi

echo "📊 相对丰度表目录：${RELATIVE_DIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 Top 物种数量：${TOP_N}"
echo "📊 分析层级：$(IFS=,; echo "${SELECTED_LEVELS[*]}")"
echo ""

# heatmapData.py 的 --outdir 为输出文件名前缀（如 cluster -> cluster.p.txt）
CLUSTER_PREFIX="cluster"

step=0
total="${#SELECTED_LEVELS[@]}"
for level_name in "${SELECTED_LEVELS[@]}"; do
    level="${LEVEL_TO_CODE[$level_name]}"
    step=$((step + 1))

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 分析 ${level_name} 水平..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    rel_table="${RELATIVE_DIR}/asv_table.${level}.relative.xls"
    if [ ! -f "${rel_table}" ]; then
        echo "  ⚠️  跳过 ${level_name}：未找到 ${rel_table}"
        echo ""
        continue
    fi

    echo "[1/3] ${level_name}: 生成热图数据..."
    "${PYTHON_BIN}" "${HEATMAP_DATA_PY}" \
        --relative "${rel_table}" \
        --top "${TOP_N}" \
        --level "${level}" \
        --outdir "${CLUSTER_PREFIX}"

    echo "[2/3] ${level_name}: 绘制热图..."
    "${RSCRIPT_BIN}" "${HEATMAP_PLOT_R}" \
        --relative "${CLUSTER_PREFIX}.${level}.txt" \
        --taxa "${CLUSTER_PREFIX}.${level}__p.list" \
        --level "${level}" \
        --group "${GROUP_FILE}" \
        --outdir "${CLUSTER_PREFIX}"

    echo "[3/3] ${level_name}: 转换 PDF → PNG..."
    "${CONVERT_BIN}" -density 200 "${CLUSTER_PREFIX}.${level}.pdf" "${CLUSTER_PREFIX}.${level}.png" 2>/dev/null || true

    echo "  ✅ ${level_name} 水平热图完成"
    echo ""
done

echo "✅ 物种组成热图（样本水平）完成"
echo ""
echo "📊 输出文件:"
for level_name in "${SELECTED_LEVELS[@]}"; do
    level="${LEVEL_TO_CODE[$level_name]}"
    echo "   - ${CLUSTER_PREFIX}.${level}.png/pdf: ${level_name} 水平热图"
done
if [ "${GENERATED_RELATIVE}" -eq 1 ]; then
    echo "   - Relative/: 由 asv_table.even.txt 生成的相对丰度表"
fi
echo ""
