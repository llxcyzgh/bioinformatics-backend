#!/bin/bash
# step5_alpha_div.sh - Alpha 多样性差异分析脚本
# 用法：bash step5_alpha_div.sh -i <alpha_diversity_index.txt> -g <group.list> -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# Perl 脚本路径
ALPHA_DIV_ANOVA_TEST_PL="${ALPHA_DIV_ANOVA_TEST_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_div/Alpha_div_anova_test.pl}"
BEESWARM_PL="${BEESWARM_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_div/beeswarm.pl}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

# 验证 Perl 脚本存在
if [ ! -f "${COLOR_DEFINED_PL}" ]; then
    echo "❌ 错误：color_defined.pl 不存在：${COLOR_DEFINED_PL}"
    echo "   可通过环境变量覆盖，例如：export COLOR_DEFINED_PL=\"/your/path/to/color_defined.pl\""
    exit 1
fi

INPUT_FILE=""
GROUP_FILE=""

OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_FILE="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
                -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step5_alpha_div.sh -i <alpha_diversity_index.txt> -g <group.list>"
            echo ""
            echo "参数:"
            echo "  -i, --input    Alpha 多样性指数表路径"
            echo "  -g, --group    样本分组文件路径"
            echo "  -o, --output     输出目录"

            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INPUT_FILE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ ! -f "${INPUT_FILE}" ] && { echo "❌ 错误：指数表不存在：${INPUT_FILE}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# ----- 路径转绝对路径（cd 输出目录前） -----
INPUT_FILE="$(abs_path_file "${INPUT_FILE}")"
GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "Alpha 多样性差异分析"
echo "=========================================="
echo ""

echo "📊 Alpha 多样性指数表：${INPUT_FILE}"
echo "📊 分组文件：${GROUP_FILE}"
echo ""

# Step 0: 调用 color_defined.pl 生成 group_col.list
echo "[0/5] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

# Step 1: ANOVA 检验
echo "[1/5] ANOVA 检验..."
"${PERL_BIN}" "${ALPHA_DIV_ANOVA_TEST_PL}" --method 12 "${INPUT_FILE}" "${GROUP_COL_LIST}"

# Step 2: 绘制 Observed Features 蜜蜂群图
echo "[2/5] 绘制 Observed Features 蜜蜂群图..."
mkdir -p beeswarm
"${PERL_BIN}" "${BEESWARM_PL}" \
    --alpha_index "${INPUT_FILE}" \
    --group_col "${GROUP_COL_LIST}" \
    --alpha_div "." \
    --group "${GROUP_FILE}" \
    --type 'observed_features' \
    --outdir './beeswarm'

# Step 3: 绘制 Shannon 指数蜜蜂群图
echo "[3/5] 绘制 Shannon 指数蜜蜂群图..."
"${PERL_BIN}" "${BEESWARM_PL}" \
    --alpha_index "${INPUT_FILE}" \
    --group_col "${GROUP_COL_LIST}" \
    --alpha_div "." \
    --group "${GROUP_FILE}" \
    --type 'shannon' \
    --outdir './beeswarm'

# Step 4: 合并图片
echo "[4/5] 合并 Alpha 多样性差异图..."
"${CONVERT_BIN}" +append observed_features.pdf shannon.pdf alpha_diff.pdf 2>/dev/null || true
"${CONVERT_BIN}" +append observed_features.png shannon.png alpha_diff.png 2>/dev/null || true

# 清理临时文件
rm -f "${GROUP_COL_LIST}"

echo ""
echo "✅ Alpha 多样性差异分析完成"
echo ""
echo "📊 输出文件:"
echo "   - anova_test.txt: ANOVA 检验结果"
echo "   - beeswarm/observed_features.svg/png: Observed Features 蜜蜂群图"
echo "   - beeswarm/shannon.svg/png: Shannon 指数蜜蜂群图"
echo "   - alpha_diff.svg/png: Alpha 多样性差异合并图"
echo ""
