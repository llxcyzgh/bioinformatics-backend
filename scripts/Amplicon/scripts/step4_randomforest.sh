#!/bin/bash
# step4_randomforest.sh - 随机森林分析脚本
# 用法：bash step4_randomforest.sh -i <Relative/|asv_table.even.txt> -g <group.list> -r <rf.list> [-l <levels>] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"
RF_ROC_PL="${RF_ROC_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/rf_roc/rf_roc.pl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

MIN_SAMPLES="${MIN_SAMPLES:-15}"

declare -A RANK_TO_DIR=(
    ["p"]="phylum"
    ["c"]="class"
    ["o"]="order"
    ["f"]="family"
    ["g"]="genus"
    ["s"]="species"
    ["otu"]="otu"
)
ALL_RANK_CODES=(p c o f g s otu)

# 从 group.list 统计某组样本数（2 列取第 2 列，3 列及以上取最后一列）
_count_group_samples() {
    local group_name="$1"
    local group_file="$2"
    awk -F'\t' -v g="${group_name}" '
        NF >= 2 && $1 !~ /^#/ {
            grp = (NF >= 3) ? $NF : $2
            if (grp == g) n++
        }
        END { print n + 0 }
    ' "${group_file}"
}

# 校验 rf.list 中每组对比的样本数是否满足 MIN_SAMPLES
_check_rf_sample_sizes() {
    local rf_file="$1"
    local group_file="$2"
    local g1 g2 n1 n2
    local failed=0

    while IFS=$'\t' read -r g1 g2 _ || [ -n "${g1}" ]; do
        g1="$(echo "${g1}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        g2="$(echo "${g2}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -z "${g1}" ] && continue
        [[ "${g1}" =~ ^# ]] && continue
        [ -z "${g2}" ] && continue

        n1="$(_count_group_samples "${g1}" "${group_file}")"
        n2="$(_count_group_samples "${g2}" "${group_file}")"

        if [ "${n1}" -lt "${MIN_SAMPLES}" ]; then
            echo "❌ 对比 ${g1} vs ${g2}：组 ${g1} 样本数 ${n1}，少于 ${MIN_SAMPLES} 个"
            failed=1
        fi
        if [ "${n2}" -lt "${MIN_SAMPLES}" ]; then
            echo "❌ 对比 ${g1} vs ${g2}：组 ${g2} 样本数 ${n2}，少于 ${MIN_SAMPLES} 个"
            failed=1
        fi
    done < "${rf_file}"

    if [ "${failed}" -eq 1 ]; then
        echo "❌ 随机森林要求对比组内样本均不少于 ${MIN_SAMPLES} 个，已终止分析"
        exit 1
    fi
}

_parse_levels() {
    local input="$1"
    local token code
    declare -A seen=()
    SELECTED_RANKS=()

    if [ -z "${input}" ]; then
        SELECTED_RANKS=("${ALL_RANK_CODES[@]}")
        return 0
    fi

    local IFS=','
    for token in ${input}; do
        token="$(echo "${token}" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -z "${token}" ] && continue
        case "${token}" in
            phylum|p) code="p" ;;
            class|c) code="c" ;;
            order|o) code="o" ;;
            family|f) code="f" ;;
            genus|g) code="g" ;;
            species|s) code="s" ;;
            otu|asv) code="otu" ;;
            *)
                echo "❌ 错误：未知分类层级：${token}"
                echo "   可选：phylum(p), class(c), order(o), family(f), genus(g), species(s), otu"
                exit 1
                ;;
        esac
        if [ -z "${seen[$code]}" ]; then
            seen[$code]=1
            SELECTED_RANKS+=("${code}")
        fi
    done

    if [ "${#SELECTED_RANKS[@]}" -eq 0 ]; then
        echo "❌ 错误：-l 未指定有效分类层级"
        exit 1
    fi
}

_build_rank_arg() {
    local IFS=','
    echo "${SELECTED_RANKS[*]}"
}

_pick_merge_dir() {
    local code
    for code in g otu s f o c p; do
        for selected in "${SELECTED_RANKS[@]}"; do
            if [ "${selected}" = "${code}" ]; then
                echo "${RANK_TO_DIR[$code]}"
                return 0
            fi
        done
    done
}

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -x "${PERL_BIN}" ]; then
    echo "❌ 错误：PERL_BIN 不存在：${PERL_BIN}"
    exit 1
fi
if [ ! -f "${STAT_OTU_TAB_PL}" ]; then
    echo "❌ 错误：STAT_OTU_TAB_PL 不存在：${STAT_OTU_TAB_PL}"
    exit 1
fi
if [ ! -f "${RF_ROC_PL}" ]; then
    echo "❌ 错误：RF_ROC_PL 不存在：${RF_ROC_PL}"
    exit 1
fi
if [ ! -x "${CONVERT_BIN}" ]; then
    echo "❌ 错误：CONVERT_BIN 不存在：${CONVERT_BIN}"
    exit 1
fi

INPUT_PATH=""
GROUP_FILE=""
RF_LIST=""
LEVELS_ARG=""
SELECTED_RANKS=()
OUTPUT_DIR=""
GENERATED_RELATIVE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input|--indir) INPUT_PATH="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -r|--rf-list) RF_LIST="$2"; shift 2 ;;
        -l|--levels) LEVELS_ARG="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step4_randomforest.sh -i <Relative/|asv_table.even.txt> -g <group.list> -r <rf.list> [-l <levels>] -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -i, --input      Relative/ 目录，或 step3 输出的 asv_table.even.txt"
            echo "  -g, --group      样本分组文件路径"
            echo "  -r, --rf-list    Random Forest 对比列表路径"
            echo "  -l, --levels     分析层级，逗号分隔（默认：p,c,o,f,g,s,otu）"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            echo ""
            echo "层级可选：phylum(p), class(c), order(o), family(f), genus(g), species(s), otu"
            echo "示例：-l phylum,genus  或  -l p,g,otu"
            echo ""
            echo "说明：rf.list 中每组对比要求组内样本均不少于 ${MIN_SAMPLES} 个（可用 MIN_SAMPLES 环境变量覆盖）"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

if [ -z "${INPUT_PATH}" ]; then echo "❌ 错误：必须提供 -i"; exit 1; fi
if [ -z "${GROUP_FILE}" ]; then echo "❌ 错误：必须提供 -g"; exit 1; fi
if [ -z "${RF_LIST}" ]; then echo "❌ 错误：必须提供 -r"; exit 1; fi
if [ -z "${OUTPUT_DIR}" ]; then echo "❌ 错误：必须提供 -o"; exit 1; fi
if [ ! -f "${GROUP_FILE}" ]; then echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; fi
if [ ! -f "${RF_LIST}" ]; then echo "❌ 错误：对比列表不存在：${RF_LIST}"; exit 1; fi
if [ ! -f "${INPUT_PATH}" ] && [ ! -d "${INPUT_PATH}" ]; then
    echo "❌ 错误：输入路径不存在：${INPUT_PATH}"
    echo "   -i 可传 Relative/ 目录或 asv_table.even.txt 文件"
    exit 1
fi

_parse_levels "${LEVELS_ARG}"
RANK_ARG="$(_build_rank_arg)"
MERGE_DIR="$(_pick_merge_dir)"

GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
RF_LIST="$(abs_path_file "${RF_LIST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"

_check_rf_sample_sizes "${RF_LIST}" "${GROUP_FILE}"

# 在 cd 输出目录前解析 -i（避免相对路径在 cd 后失效）
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
    echo "随机森林分析"
    echo "=========================================="
    echo ""
    echo "📊 均一化 ASV 表：${EVEN_TABLE}"
    echo "[0/2] 生成 Relative 相对丰度表..."
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
    echo "随机森林分析"
    echo "=========================================="
    echo ""
fi

echo "📊 相对丰度表目录：${RELATIVE_DIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 对比列表：${RF_LIST}"
echo "📊 分析层级：${RANK_ARG}"
echo "📊 最小组样本数：${MIN_SAMPLES}"
echo ""

echo "[1/2] 执行随机森林 + ROC 曲线分析..."
"${PERL_BIN}" "${RF_ROC_PL}" \
    --rf "${RF_LIST}" \
    --indir "${RELATIVE_DIR}" \
    --rank "${RANK_ARG}" \
    --group "${GROUP_FILE}" \
    --outdir ./

echo "[2/2] 合并重要性图和 AUC 曲线（${MERGE_DIR}/）..."

"${CONVERT_BIN}" +append \
    "${MERGE_DIR}"/1*/30/impplot_MeanDecreaseAccuracy30.png \
    "${MERGE_DIR}"/1_*/30/impplot_MeanDecreaseGin30.png \
    tax_show_ea.png 2>/dev/null || true

"${CONVERT_BIN}" +append \
    "${MERGE_DIR}"/1*/30/impplot_MeanDecreaseAccuracy30.pdf \
    "${MERGE_DIR}"/1_*/30/impplot_MeanDecreaseGin30.pdf \
    tax_show_ea.pdf 2>/dev/null || true

"${CONVERT_BIN}" +append \
    "${MERGE_DIR}"/1_*/trainset_auc.png \
    "${MERGE_DIR}"/1_*/testset_auc.png \
    auc.png 2>/dev/null || true

"${CONVERT_BIN}" +append \
    "${MERGE_DIR}"/1_*/trainset_auc.pdf \
    "${MERGE_DIR}"/1_*/testset_auc.pdf \
    auc.pdf 2>/dev/null || true

echo ""
echo "✅ 随机森林分析完成"
echo ""
echo "📊 输出文件（各所选层级子目录：$(for code in "${SELECTED_RANKS[@]}"; do echo -n "${RANK_TO_DIR[$code]} "; done)）:"
for code in "${SELECTED_RANKS[@]}"; do
    dir="${RANK_TO_DIR[$code]}"
    echo "   - ${dir}/impplot_MeanDecreaseAccuracy*.png/pdf: ${dir} 重要性图（准确率）"
    echo "   - ${dir}/impplot_MeanDecreaseGini*.png/pdf: ${dir} 重要性图（基尼系数）"
    echo "   - ${dir}/trainset_auc.png/pdf, ${dir}/testset_auc.png/pdf: ${dir} AUC 曲线"
done
echo "   - tax_show_ea.png/pdf: 重要性图合并图（${MERGE_DIR}/）"
echo "   - auc.png/pdf: AUC 曲线合并图（${MERGE_DIR}/）"
if [ "${GENERATED_RELATIVE}" -eq 1 ]; then
    echo "   - Relative/: 由 asv_table.even.txt 生成的相对丰度表"
fi
echo ""
