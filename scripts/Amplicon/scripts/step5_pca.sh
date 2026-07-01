#!/bin/bash
# step5_pca.sh - PCA 主成分分析脚本
# 用法：bash step5_pca.sh -i <asv_table.even.txt|Relative/|*.relative.xls> -g <group.list> [-l <levels>] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"
UOA_R_PL="${UOA_R_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCA/UOA.R}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"

declare -A LEVEL_TO_CODE=(
    ["kingdom"]="k"
    ["phylum"]="p"
    ["class"]="c"
    ["order"]="o"
    ["family"]="f"
    ["genus"]="g"
    ["species"]="s"
    ["otu"]="otu"
    ["asv"]="otu"
)
declare -A CODE_TO_NAME=(
    ["k"]="kingdom"
    ["p"]="phylum"
    ["c"]="class"
    ["o"]="order"
    ["f"]="family"
    ["g"]="genus"
    ["s"]="species"
    ["otu"]="otu"
)
DEFAULT_LEVELS=(genus)

_parse_levels() {
    local input="$1"
    local token level
    declare -A seen=()
    SELECTED_LEVELS=()

    if [ -z "${input}" ]; then
        SELECTED_LEVELS=("${DEFAULT_LEVELS[@]}")
        return 0
    fi

    local IFS=','
    for token in ${input}; do
        token="$(echo "${token}" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -z "${token}" ] && continue
        case "${token}" in
            kingdom|k) level="kingdom" ;;
            phylum|p) level="phylum" ;;
            class|c) level="class" ;;
            order|o) level="order" ;;
            family|f) level="family" ;;
            genus|g) level="genus" ;;
            species|s) level="species" ;;
            otu|asv) level="otu" ;;
            *)
                echo "❌ 错误：未知分类层级：${token}"
                echo "   可选：kingdom(k), phylum(p), class(c), order(o), family(f), genus(g), species(s), otu(asv)"
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

_level_from_relative_file() {
    local file="$1"
    local base
    base="$(basename "${file}")"
    case "${base}" in
        asv_table.relative.xls) echo "otu" ;;
        asv_table.k.relative.xls) echo "k" ;;
        asv_table.p.relative.xls) echo "p" ;;
        asv_table.c.relative.xls) echo "c" ;;
        asv_table.o.relative.xls) echo "o" ;;
        asv_table.f.relative.xls) echo "f" ;;
        asv_table.g.relative.xls) echo "g" ;;
        asv_table.s.relative.xls) echo "s" ;;
        *) echo "" ;;
    esac
}

_relative_table_path() {
    local relative_dir="$1"
    local level_code="$2"
    if [ "${level_code}" = "otu" ]; then
        echo "${relative_dir}/asv_table.relative.xls"
    else
        echo "${relative_dir}/asv_table.${level_code}.relative.xls"
    fi
}

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

for bin in RSCRIPT_BIN CONVERT_BIN PERL_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        exit 1
    fi
done
for tool in STAT_OTU_TAB_PL UOA_R_PL COLOR_DEFINED_PL; do
    if [ ! -f "${!tool}" ]; then
        echo "❌ 错误：${tool} 不存在：${!tool}"
        exit 1
    fi
done

INPUT_PATH=""
GROUP_FILE=""
LEVELS_ARG=""
SELECTED_LEVELS=()
OUTPUT_DIR=""
GENERATED_RELATIVE=0
INPUT_MODE=""
SINGLE_RELATIVE_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_PATH="$2"; shift 2 ;;
        -t|--table) INPUT_PATH="$2"; shift 2 ;;
        -r|--relative) INPUT_PATH="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -l|--levels) LEVELS_ARG="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step5_pca.sh -i <input> -g <group.list> [-l <levels>] -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -i, --input      asv_table.even.txt、Relative/ 目录，或 *.relative.xls 文件"
            echo "  -t, --table      同 -i（均一化 ASV 表）"
            echo "  -r, --relative   同 -i（相对丰度表或 Relative/ 目录）"
            echo "  -g, --group      样本分组文件路径"
            echo "  -l, --levels     分析层级，逗号分隔（默认：genus）"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            echo ""
            echo "层级可选：kingdom(k), phylum(p), class(c), order(o), family(f), genus(g), species(s), otu(asv)"
            echo "示例：-l genus,phylum  或  -l g,p"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${INPUT_PATH}" ] && { echo "❌ 错误：必须提供 -i（或 -t / -r）"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
if [ ! -f "${INPUT_PATH}" ] && [ ! -d "${INPUT_PATH}" ]; then
    echo "❌ 错误：输入路径不存在：${INPUT_PATH}"
    echo "   当前工作目录：$(pwd)"
    echo "   -i 可传 asv_table.even.txt、Relative/ 目录或 asv_table.*.relative.xls 文件"
    exit 1
fi
if [ ! -f "${GROUP_FILE}" ]; then
    echo "❌ 错误：分组文件不存在：${GROUP_FILE}"
    echo "   当前工作目录：$(pwd)"
    exit 1
fi

if [ -f "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_file "${INPUT_PATH}")"
    base="$(basename "${INPUT_PATH}")"
    if [ "${base}" = "asv_table.even.txt" ]; then
        INPUT_MODE="even"
    elif [[ "${base}" == *.relative.xls ]]; then
        INPUT_MODE="relative_file"
        SINGLE_RELATIVE_FILE="${INPUT_PATH}"
    else
        echo "❌ 错误：无法识别输入文件：${INPUT_PATH}"
        echo "   请传入 asv_table.even.txt 或 asv_table.*.relative.xls"
        exit 1
    fi
elif [ -d "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_dir "${INPUT_PATH}")"
    base="$(basename "${INPUT_PATH}")"
    if [ "${base}" = "Relative" ] || [ -f "${INPUT_PATH}/asv_table.g.relative.xls" ] || [ -f "${INPUT_PATH}/asv_table.relative.xls" ]; then
        INPUT_MODE="relative_dir"
    else
        echo "❌ 错误：无法识别目录类型：${INPUT_PATH}"
        echo "   请传入 Relative/ 目录"
        exit 1
    fi
fi

if [ "${INPUT_MODE}" = "relative_file" ]; then
    _parse_levels "${LEVELS_ARG}"
    inferred="$(_level_from_relative_file "${SINGLE_RELATIVE_FILE}")"
    if [ -n "${inferred}" ]; then
        inferred_name="${CODE_TO_NAME[$inferred]}"
        if [ -n "${LEVELS_ARG}" ]; then
            found=0
            for level_name in "${SELECTED_LEVELS[@]}"; do
                [ "${LEVEL_TO_CODE[$level_name]}" = "${inferred}" ] && found=1
            done
            if [ "${found}" -eq 0 ]; then
                echo "⚠️  输入文件为 ${inferred_name} 水平，与 -l 不一致，将仅分析该文件"
            fi
        fi
        SELECTED_LEVELS=("${inferred_name}")
    elif [ -z "${LEVELS_ARG}" ]; then
        echo "❌ 错误：无法从文件名识别分类层级，请使用 -l 指定"
        exit 1
    fi
else
    _parse_levels "${LEVELS_ARG}"
fi

GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "PCA 主成分分析"
echo "=========================================="
echo ""

if [ "${INPUT_MODE}" = "even" ]; then
    RELATIVE_DIR="${OUTPUT_DIR}/Relative"
    echo "📊 均一化 ASV 表：${INPUT_PATH}"
    echo "[0/N] 生成 Relative 相对丰度表..."
    mkdir -p "${RELATIVE_DIR}"
    "${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
        "${INPUT_PATH}" \
        --prefix "${RELATIVE_DIR}/asv_table"
    echo "  ✅ Relative 目录：${RELATIVE_DIR}"
    GENERATED_RELATIVE=1
elif [ "${INPUT_MODE}" = "relative_dir" ]; then
    RELATIVE_DIR="${INPUT_PATH}"
elif [ "${INPUT_MODE}" = "relative_file" ]; then
    RELATIVE_DIR="$(dirname "${SINGLE_RELATIVE_FILE}")"
fi

echo "📊 分组文件：${GROUP_FILE}"
echo "📊 分析层级：$(IFS=,; echo "${SELECTED_LEVELS[*]}")"
if [ "${INPUT_MODE}" != "even" ]; then
    echo "📊 相对丰度目录：${RELATIVE_DIR}"
fi
echo ""

echo "[0/N] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

multi_level=0
[ "${#SELECTED_LEVELS[@]}" -gt 1 ] && multi_level=1
completed=0

for level_name in "${SELECTED_LEVELS[@]}"; do
    level="${LEVEL_TO_CODE[$level_name]}"

    if [ "${INPUT_MODE}" = "relative_file" ]; then
        rel_table="${SINGLE_RELATIVE_FILE}"
    else
        rel_table="$(_relative_table_path "${RELATIVE_DIR}" "${level}")"
    fi

    if [ ! -f "${rel_table}" ]; then
        echo "  ⚠️  跳过 ${level_name}：未找到 ${rel_table}"
        echo ""
        continue
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 PCA 分析：${level_name} 水平"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 相对丰度表：${rel_table}"

    echo "[1/2] 绘制 PCA 排序图..."
    "${RSCRIPT_BIN}" "${UOA_R_PL}" --rFile "${rel_table}" --gcFile "${GROUP_COL_LIST}" --method pca --workdir .

    echo "[2/2] 转换 PDF → PNG..."
    "${CONVERT_BIN}" -density 300 UOA_pca.pdf UOA_pca.png 2>/dev/null || true

    if [ "${multi_level}" -eq 1 ]; then
        for ext in pdf png svg; do
            [ -f "UOA_pca.${ext}" ] && mv -f "UOA_pca.${ext}" "UOA_pca.${level}.${ext}"
        done
        echo "  ✅ ${level_name} 水平完成：UOA_pca.${level}.pdf/png"
    else
        echo "  ✅ ${level_name} 水平完成：UOA_pca.pdf/png"
    fi
    echo ""
    completed=$((completed + 1))

    [ "${INPUT_MODE}" = "relative_file" ] && break
done

rm -f "${GROUP_COL_LIST}"

if [ "${completed}" -eq 0 ]; then
    echo "❌ 错误：未找到任何所选层级的相对丰度表"
    exit 1
fi

echo "✅ PCA 主成分分析完成"
echo ""
echo "📊 输出文件:"
for level_name in "${SELECTED_LEVELS[@]}"; do
    level="${LEVEL_TO_CODE[$level_name]}"
    if [ "${multi_level}" -eq 1 ]; then
        echo "   - UOA_pca.${level}.png/pdf: ${level_name} 水平 PCA 排序图"
    else
        echo "   - UOA_pca.png/pdf: ${level_name} 水平 PCA 排序图"
    fi
    [ "${INPUT_MODE}" = "relative_file" ] && break
done
if [ "${GENERATED_RELATIVE}" -eq 1 ]; then
    echo "   - Relative/: 由 asv_table.even.txt 生成的相对丰度表"
fi
echo ""
