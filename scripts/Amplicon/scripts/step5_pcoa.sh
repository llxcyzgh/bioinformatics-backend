#!/bin/bash
# step5_pcoa.sh - PCoA 主坐标分析脚本
# 用法：bash step5_pcoa.sh -i <BetaData/|ordination.txt> [-d <distances>] -g <group.list> -o <output_dir>
#       bash step5_pcoa.sh -w <weighted_pc.txt> -wu <unweighted_pc.txt> -g <group.list> -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
PCOA_PL="${PCOA_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/betaAnalysis/pcoa.pl}"
PCOA_R_PL="${PCOA_R_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCoA/plot_PCoA.R}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"

declare -A DIST_ORDINATION_REL=(
    ["unweighted_unifrac"]="unweighted_unifrac_pcoa_results_qza/ordination.txt"
    ["weighted_unifrac"]="weighted_unifrac_pcoa_results_qza/ordination.txt"
    ["jaccard"]="jaccard_pcoa_results_qza/ordination.txt"
    ["bray_curtis"]="bray_curtis_pcoa_results_qza/ordination.txt"
)
DEFAULT_DISTANCES=(unweighted_unifrac weighted_unifrac)

_parse_distances() {
    local input="$1"
    local token dist
    declare -A seen=()
    SELECTED_DISTANCES=()

    if [ -z "${input}" ]; then
        SELECTED_DISTANCES=("${DEFAULT_DISTANCES[@]}")
        return 0
    fi

    local IFS=','
    for token in ${input}; do
        token="$(echo "${token}" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/-/_/g')"
        [ -z "${token}" ] && continue
        case "${token}" in
            unweighted_unifrac|wu|unweighted) dist="unweighted_unifrac" ;;
            weighted_unifrac|w|weighted) dist="weighted_unifrac" ;;
            jaccard|j) dist="jaccard" ;;
            bray_curtis|bray|bc) dist="bray_curtis" ;;
            *)
                echo "❌ 错误：未知距离类型：${token}"
                echo "   可选：unweighted_unifrac(wu), weighted_unifrac(w), jaccard(j), bray_curtis(bc)"
                exit 1
                ;;
        esac
        if [ -z "${seen[$dist]}" ]; then
            seen[$dist]=1
            SELECTED_DISTANCES+=("${dist}")
        fi
    done

    if [ "${#SELECTED_DISTANCES[@]}" -eq 0 ]; then
        echo "❌ 错误：-d 未指定有效距离类型"
        exit 1
    fi
}

_infer_distance_from_path() {
    local path="$1"
    case "${path}" in
        *unweighted_unifrac_pcoa*) echo "unweighted_unifrac" ;;
        *weighted_unifrac_pcoa*) echo "weighted_unifrac" ;;
        *jaccard_pcoa*) echo "jaccard" ;;
        *bray_curtis_pcoa*) echo "bray_curtis" ;;
        *) echo "" ;;
    esac
}

_resolve_ordination() {
    local beta_dir="$1"
    local dist="$2"
    echo "${beta_dir}/${DIST_ORDINATION_REL[$dist]}"
}

_is_beta_data_dir() {
    local dir="$1"
    local dist
    for dist in unweighted_unifrac weighted_unifrac jaccard bray_curtis; do
        [ -f "$(_resolve_ordination "${dir}" "${dist}")" ] && return 0
    done
    return 1
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
for tool in PCOA_PL PCOA_R_PL COLOR_DEFINED_PL; do
    if [ ! -f "${!tool}" ]; then
        echo "❌ 错误：${tool} 不存在：${!tool}"
        exit 1
    fi
done

INPUT_PATH=""
DISTANCES_ARG=""
SELECTED_DISTANCES=()
GROUP_FILE=""
WEIGHTED_PC=""
UNWEIGHTED_PC=""
OUTPUT_DIR=""
INPUT_MODE=""
SINGLE_ORDINATION=""
LEGACY_PC=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_PATH="$2"; shift 2 ;;
        -d|--distances) DISTANCES_ARG="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -w|--weighted) WEIGHTED_PC="$2"; shift 2 ;;
        -wu|--unweighted) UNWEIGHTED_PC="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step5_pcoa.sh -i <BetaData/|ordination.txt> [-d <distances>] -g <group.list> -o <output_dir>"
            echo "      bash step5_pcoa.sh -w <weighted_pc.txt> [-wu <unweighted_pc.txt>] -g <group.list> -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -i, --input       step3_beta_data 输出的 BetaData/ 目录，或 ordination.txt 文件"
            echo "  -d, --distances   距离类型，逗号分隔（默认：unweighted_unifrac,weighted_unifrac）"
            echo "  -g, --group       样本分组文件路径"
            echo "  -w, --weighted    已生成的 weighted_unifrac_pc.txt（兼容旧用法）"
            echo "  -wu, --unweighted 已生成的 unweighted_unifrac_pc.txt（兼容旧用法）"
            echo "  -o, --output      输出目录"
            echo "  -h, --help        显示帮助"
            echo ""
            echo "距离可选：unweighted_unifrac(wu), weighted_unifrac(w), jaccard(j), bray_curtis(bc)"
            echo "示例：-d weighted_unifrac,jaccard  或  -d w,j"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

if [ -z "${INPUT_PATH}" ] && [ -z "${WEIGHTED_PC}" ] && [ -z "${UNWEIGHTED_PC}" ]; then
    echo "❌ 错误：必须提供 -i（BetaData/ 或 ordination.txt），或 -w/-wu（pc 坐标文件）"
    exit 1
fi

if [ -n "${INPUT_PATH}" ]; then
    if [ ! -f "${INPUT_PATH}" ] && [ ! -d "${INPUT_PATH}" ]; then
        echo "❌ 错误：输入路径不存在：${INPUT_PATH}"
        echo "   当前工作目录：$(pwd)"
        exit 1
    fi
    if [ -f "${INPUT_PATH}" ]; then
        INPUT_PATH="$(abs_path_file "${INPUT_PATH}")"
        base="$(basename "${INPUT_PATH}")"
        if [ "${base}" = "ordination.txt" ]; then
            INPUT_MODE="ordination_file"
            SINGLE_ORDINATION="${INPUT_PATH}"
        else
            echo "❌ 错误：无法识别输入文件：${INPUT_PATH}"
            echo "   请传入 ordination.txt 或 BetaData/ 目录"
            exit 1
        fi
    elif [ -d "${INPUT_PATH}" ]; then
        INPUT_PATH="$(abs_path_dir "${INPUT_PATH}")"
        if _is_beta_data_dir "${INPUT_PATH}"; then
            INPUT_MODE="beta_dir"
        else
            echo "❌ 错误：目录中未找到 *_pcoa_results_qza/ordination.txt：${INPUT_PATH}"
            exit 1
        fi
    fi
fi

if [ "${INPUT_MODE}" = "ordination_file" ]; then
    inferred="$(_infer_distance_from_path "${SINGLE_ORDINATION}")"
    if [ -n "${inferred}" ]; then
        if [ -n "${DISTANCES_ARG}" ]; then
            _parse_distances "${DISTANCES_ARG}"
            found=0
            for dist in "${SELECTED_DISTANCES[@]}"; do
                [ "${dist}" = "${inferred}" ] && found=1
            done
            if [ "${found}" -eq 0 ]; then
                echo "⚠️  输入 ordination.txt 为 ${inferred}，与 -d 不一致，将仅分析该距离"
            fi
        fi
        SELECTED_DISTANCES=("${inferred}")
    else
        _parse_distances "${DISTANCES_ARG}"
        if [ "${#SELECTED_DISTANCES[@]}" -ne 1 ]; then
            echo "❌ 错误：单个 ordination.txt 输入时请用 -d 指定一个距离类型"
            exit 1
        fi
    fi
elif [ "${INPUT_MODE}" = "beta_dir" ]; then
    _parse_distances "${DISTANCES_ARG}"
else
    SELECTED_DISTANCES=()
    [ -n "${WEIGHTED_PC}" ] && SELECTED_DISTANCES+=("weighted_unifrac")
    [ -n "${UNWEIGHTED_PC}" ] && SELECTED_DISTANCES+=("unweighted_unifrac")
    if [ "${#SELECTED_DISTANCES[@]}" -eq 0 ]; then
        echo "❌ 错误：必须提供 -w 和/或 -wu"
        exit 1
    fi
    INPUT_MODE="legacy_pc"
fi

if [ -n "${WEIGHTED_PC}" ]; then
    [ ! -f "${WEIGHTED_PC}" ] && { echo "❌ 错误：Weighted PCoA 坐标不存在：${WEIGHTED_PC}"; exit 1; }
    WEIGHTED_PC="$(abs_path_file "${WEIGHTED_PC}")"
    LEGACY_PC[weighted_unifrac]="${WEIGHTED_PC}"
fi
if [ -n "${UNWEIGHTED_PC}" ]; then
    [ ! -f "${UNWEIGHTED_PC}" ] && { echo "❌ 错误：Unweighted PCoA 坐标不存在：${UNWEIGHTED_PC}"; exit 1; }
    UNWEIGHTED_PC="$(abs_path_file "${UNWEIGHTED_PC}")"
    LEGACY_PC[unweighted_unifrac]="${UNWEIGHTED_PC}"
fi

GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "PCoA 主坐标分析"
echo "=========================================="
echo ""

if [ "${INPUT_MODE}" = "beta_dir" ]; then
    echo "📊 Beta 数据目录：${INPUT_PATH}"
elif [ "${INPUT_MODE}" = "ordination_file" ]; then
    echo "📊 ordination.txt：${SINGLE_ORDINATION}"
elif [ "${INPUT_MODE}" = "legacy_pc" ]; then
    [ -n "${WEIGHTED_PC}" ] && echo "📊 Weighted UniFrac PC：${WEIGHTED_PC}"
    [ -n "${UNWEIGHTED_PC}" ] && echo "📊 Unweighted UniFrac PC：${UNWEIGHTED_PC}"
fi
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 分析距离：$(IFS=,; echo "${SELECTED_DISTANCES[*]}")"
echo ""

echo "[0/N] 生成颜色配置文件..."
GROUP_COL_LIST="${OUTPUT_DIR}/group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：group_col.list"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

completed=0
step=0
total="${#SELECTED_DISTANCES[@]}"

for dist in "${SELECTED_DISTANCES[@]}"; do
    step=$((step + 1))
    dist_dir="${OUTPUT_DIR}/${dist}"
    pc_file="${dist_dir}/${dist}_pc.txt"
    ordination=""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 PCoA 分析：${dist}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    mkdir -p "${dist_dir}"

    if [ -n "${LEGACY_PC[$dist]}" ]; then
        pc_file="${LEGACY_PC[$dist]}"
        echo "📊 使用已有 PC 坐标：${pc_file}"
    elif [ "${INPUT_MODE}" = "ordination_file" ]; then
        ordination="${SINGLE_ORDINATION}"
        echo "[${step}/${total}] pcoa.pl 导出 PC 坐标..."
        "${PERL_BIN}" "${PCOA_PL}" "${ordination}" "${dist_dir}/${dist}_pc.txt"
        pc_file="${dist_dir}/${dist}_pc.txt"
        echo "  ✅ 已生成 ${pc_file}"
    elif [ "${INPUT_MODE}" = "beta_dir" ]; then
        ordination="$(_resolve_ordination "${INPUT_PATH}" "${dist}")"
        if [ ! -f "${ordination}" ]; then
            echo "  ⚠️  跳过 ${dist}：未找到 ${ordination}"
            echo ""
            continue
        fi
        echo "📊 ordination.txt：${ordination}"
        echo "[${step}/${total}] pcoa.pl 导出 PC 坐标..."
        "${PERL_BIN}" "${PCOA_PL}" "${ordination}" "${dist_dir}/${dist}_pc.txt"
        pc_file="${dist_dir}/${dist}_pc.txt"
        echo "  ✅ 已生成 ${pc_file}"
    else
        echo "  ⚠️  跳过 ${dist}：未找到输入坐标"
        echo ""
        continue
    fi

    if [ ! -f "${pc_file}" ]; then
        echo "  ⚠️  跳过 ${dist}：PC 坐标文件不存在：${pc_file}"
        echo ""
        continue
    fi

    echo "[${step}/${total}] 绘制 PCoA 排序图..."
    "${RSCRIPT_BIN}" "${PCOA_R_PL}" \
        --unifrac_pc "${pc_file}" \
        --group_col "${GROUP_COL_LIST}" \
        --outdir "${dist_dir}"

    echo "  ✅ ${dist} 完成：${dist}/PCoA12.pdf/png"
    echo ""
    completed=$((completed + 1))
done

rm -f "${GROUP_COL_LIST}"

if [ "${completed}" -eq 0 ]; then
    echo "❌ 错误：未成功完成任何距离的 PCoA 分析"
    exit 1
fi

echo "✅ PCoA 主坐标分析完成"
echo ""
echo "📊 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
for dist in "${SELECTED_DISTANCES[@]}"; do
    [ -f "${OUTPUT_DIR}/${dist}/PCoA12.pdf" ] && \
        echo "   - ${dist}/PCoA12.pdf/png: ${dist} PCoA 图"
    if [ "${INPUT_MODE}" = "beta_dir" ] || [ "${INPUT_MODE}" = "ordination_file" ]; then
        [ -f "${OUTPUT_DIR}/${dist}/${dist}_pc.txt" ] && \
            echo "   - ${dist}/${dist}_pc.txt: PC 坐标"
    fi
done
echo ""
