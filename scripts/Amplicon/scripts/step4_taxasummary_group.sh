#!/bin/bash
# step4_taxasummary_group.sh - 物种组成热图脚本（分组水平）
# 用法：bash step4_taxasummary_group.sh -i <Relative_group/|Relative/|asv_table.even.txt> [-g <group.list>] [-l <levels>] [--top <N>] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"
COMBINE_TABLE_PL="${COMBINE_TABLE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/Combine_table.pl}"
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

_generate_relative_group() {
    local relative_dir="$1"
    local group_file="$2"
    local out_dir="$3"

    mkdir -p "${out_dir}"
    for level_name in "${SELECTED_LEVELS[@]}"; do
        level="${LEVEL_TO_CODE[$level_name]}"
        src="${relative_dir}/asv_table.${level}.relative.xls"
        if [ ! -f "${src}" ]; then
            echo "  ⚠️  跳过 ${level_name}：未找到 ${src}"
            continue
        fi
        echo "  ${level_name} 水平..."
        "${PERL_BIN}" "${COMBINE_TABLE_PL}" \
            "${src}" \
            "${group_file}" \
            > "${out_dir}/asv_table_group.${level}.relative.xls"
    done
}

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

for bin in PERL_BIN PYTHON_BIN RSCRIPT_BIN CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done
for tool in STAT_OTU_TAB_PL HEATMAP_DATA_PY HEATMAP_PLOT_R; do
    if [ ! -f "${!tool}" ]; then
        echo "❌ 错误：${tool} 不存在：${!tool}"
        echo "   可通过环境变量覆盖，例如：export ${tool}=\"/your/path/to/${tool}\""
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
GENERATED_RELATIVE_GROUP=0
INPUT_MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_PATH="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -l|--levels) LEVELS_ARG="$2"; shift 2 ;;
        --top) TOP_N="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step4_taxasummary_group.sh -i <Relative_group/|Relative/|asv_table.even.txt> [-g <group.list>] [-l <levels>] [--top <N>] -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -i, --input      Relative_group/ 目录、Relative/ 目录，或 asv_table.even.txt"
            echo "  -g, --group      样本分组文件（-i 为 Relative/ 或 asv_table.even.txt 时必需）"
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

[ -z "${INPUT_PATH}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
if [ ! -f "${INPUT_PATH}" ] && [ ! -d "${INPUT_PATH}" ]; then
    echo "❌ 错误：输入路径不存在：${INPUT_PATH}"
    echo "   -i 可传 Relative_group/、Relative/ 目录或 asv_table.even.txt 文件"
    exit 1
fi

_parse_levels "${LEVELS_ARG}"

OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"

if [ -f "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_file "${INPUT_PATH}")"
    INPUT_MODE="even"
elif [ -d "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_dir "${INPUT_PATH}")"
    base="$(basename "${INPUT_PATH}")"
    if [ "${base}" = "Relative_group" ]; then
        INPUT_MODE="relative_group"
    elif [ "${base}" = "Relative" ]; then
        INPUT_MODE="relative"
    else
        if [ -f "${INPUT_PATH}/asv_table_group.p.relative.xls" ]; then
            INPUT_MODE="relative_group"
        elif [ -f "${INPUT_PATH}/asv_table.p.relative.xls" ]; then
            INPUT_MODE="relative"
        else
            echo "❌ 错误：无法识别目录类型：${INPUT_PATH}"
            echo "   请传入 Relative_group/、Relative/ 目录，或 asv_table.even.txt 文件"
            exit 1
        fi
    fi
else
    echo "❌ 错误：无法识别输入：${INPUT_PATH}"
    exit 1
fi

if [ "${INPUT_MODE}" = "even" ] || [ "${INPUT_MODE}" = "relative" ]; then
    [ -z "${GROUP_FILE}" ] && { echo "❌ 错误：-i 为 Relative/ 或 asv_table.even.txt 时必须提供 -g"; exit 1; }
    [ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }
    [ ! -f "${COMBINE_TABLE_PL}" ] && { echo "❌ 错误：COMBINE_TABLE_PL 不存在：${COMBINE_TABLE_PL}"; exit 1; }
    GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
fi

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "物种组成热图（分组水平）"
echo "=========================================="
echo ""

if [ "${INPUT_MODE}" = "even" ]; then
    RELATIVE_DIR="${OUTPUT_DIR}/Relative"
    RELATIVE_GROUP_DIR="${OUTPUT_DIR}/Relative_group"
    echo "📊 均一化 ASV 表：${INPUT_PATH}"
    echo "[0/N] 生成 Relative 相对丰度表..."
    mkdir -p "${RELATIVE_DIR}"
    "${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
        "${INPUT_PATH}" \
        --prefix "${RELATIVE_DIR}/asv_table"
    echo "  ✅ Relative 目录：${RELATIVE_DIR}"
    GENERATED_RELATIVE=1

    echo "[0/N] 生成分组相对丰度表 Relative_group..."
    _generate_relative_group "${RELATIVE_DIR}" "${GROUP_FILE}" "${RELATIVE_GROUP_DIR}"
    echo "  ✅ Relative_group 目录：${RELATIVE_GROUP_DIR}"
    GENERATED_RELATIVE_GROUP=1
elif [ "${INPUT_MODE}" = "relative" ]; then
    RELATIVE_DIR="${INPUT_PATH}"
    RELATIVE_GROUP_DIR="${OUTPUT_DIR}/Relative_group"
    echo "📊 样本相对丰度表目录：${RELATIVE_DIR}"
    echo "📊 分组文件：${GROUP_FILE}"
    echo "[0/N] 生成分组相对丰度表 Relative_group..."
    _generate_relative_group "${RELATIVE_DIR}" "${GROUP_FILE}" "${RELATIVE_GROUP_DIR}"
    echo "  ✅ Relative_group 目录：${RELATIVE_GROUP_DIR}"
    GENERATED_RELATIVE_GROUP=1
else
    RELATIVE_GROUP_DIR="${INPUT_PATH}"
fi

if [ ! -d "${RELATIVE_GROUP_DIR}" ]; then
    echo "❌ 错误：分组相对丰度表目录不存在：${RELATIVE_GROUP_DIR}"
    exit 1
fi

echo "📊 分组相对丰度表目录：${RELATIVE_GROUP_DIR}"
echo "📊 Top 物种数量：${TOP_N}"
echo "📊 分析层级：$(IFS=,; echo "${SELECTED_LEVELS[*]}")"
echo ""

CLUSTER_PREFIX="cluster"

for level_name in "${SELECTED_LEVELS[@]}"; do
    level="${LEVEL_TO_CODE[$level_name]}"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 分析 ${level_name} 水平..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    rel_table="${RELATIVE_GROUP_DIR}/asv_table_group.${level}.relative.xls"
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
        --outdir "${CLUSTER_PREFIX}"

    echo "[3/3] ${level_name}: 转换 PDF → PNG..."
    "${CONVERT_BIN}" -density 200 "${CLUSTER_PREFIX}.${level}.pdf" "${CLUSTER_PREFIX}.${level}.png" 2>/dev/null || true

    echo "  ✅ ${level_name} 水平热图完成"
    echo ""
done

echo "✅ 物种组成热图（分组水平）完成"
echo ""
echo "📊 输出文件:"
for level_name in "${SELECTED_LEVELS[@]}"; do
    level="${LEVEL_TO_CODE[$level_name]}"
    echo "   - ${CLUSTER_PREFIX}.${level}.png/pdf: ${level_name} 水平分组热图"
done
if [ "${GENERATED_RELATIVE}" -eq 1 ]; then
    echo "   - Relative/: 由 asv_table.even.txt 生成的样本相对丰度表"
fi
if [ "${GENERATED_RELATIVE_GROUP}" -eq 1 ]; then
    echo "   - Relative_group/: 由 group.list 汇总的分组相对丰度表"
fi
echo ""
