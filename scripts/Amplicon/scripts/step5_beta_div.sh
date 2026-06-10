#!/bin/bash
# step5_beta_div.sh - Beta 多样性差异分析脚本
# 用法：bash step5_beta_div.sh -u <unweighted_unifrac_dm.txt> -w <weighted_unifrac_dm.txt> -g <group.list>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# Perl 脚本路径
BETA_GROUP_TEST_PL="${BETA_GROUP_TEST_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Beta_div/Beta_group_test.pl}"
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

UNWEIGHTED_DM=""
WEIGHTED_DM=""
GROUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--unweighted) UNWEIGHTED_DM="$2"; shift 2 ;;
        -w|--weighted) WEIGHTED_DM="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step5_beta_div.sh -u <unweighted_unifrac_dm.txt> -w <weighted_unifrac_dm.txt> -g <group.list>"
            echo ""
            echo "参数:"
            echo "  -u, --unweighted  Unweighted UniFrac 距离矩阵路径"
            echo "  -w, --weighted    Weighted UniFrac 距离矩阵路径"
            echo "  -g, --group       样本分组文件路径"
            echo "  -h, --help        显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${UNWEIGHTED_DM}" ] && { echo "❌ 错误：必须提供 -u"; exit 1; }
[ -z "${WEIGHTED_DM}" ] && { echo "❌ 错误：必须提供 -w"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ ! -f "${UNWEIGHTED_DM}" ] && { echo "❌ 错误：Unweighted 距离矩阵不存在：${UNWEIGHTED_DM}"; exit 1; }
[ ! -f "${WEIGHTED_DM}" ] && { echo "❌ 错误：Weighted 距离矩阵不存在：${WEIGHTED_DM}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

echo ""
echo "=========================================="
echo "Beta 多样性差异分析"
echo "=========================================="
echo ""

echo "📊 Unweighted UniFrac 距离矩阵：${UNWEIGHTED_DM}"
echo "📊 Weighted UniFrac 距离矩阵：${WEIGHTED_DM}"
echo "📊 分组文件：${GROUP_FILE}"
echo ""

# Step 0: 调用 color_defined.pl 生成 group_col.list
echo "[0/4] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

# Step 1: Unweighted UniFrac 组间差异检验
echo "[1/4] Unweighted UniFrac 组间差异检验..."
"${PERL_BIN}" "${BETA_GROUP_TEST_PL}" \
    --method 12 \
    "${UNWEIGHTED_DM}" \
    "${GROUP_COL_LIST}" \
    --ylab unweighted_unifrac

# Step 2: Weighted UniFrac 组间差异检验
echo "[2/4] Weighted UniFrac 组间差异检验..."
"${PERL_BIN}" "${BETA_GROUP_TEST_PL}" \
    --method 12 \
    "${WEIGHTED_DM}" \
    "${GROUP_COL_LIST}" \
    --ylab weighted_unifrac

# Step 3: 合并图片
echo "[3/4] 合并 Beta 多样性差异图..."
"${CONVERT_BIN}" +append weighted_unifrac.pdf unweighted_unifrac.pdf beta_diff.pdf 2>/dev/null || true
"${CONVERT_BIN}" +append weighted_unifrac.png unweighted_unifrac.png beta_diff.png 2>/dev/null || true

# 清理临时文件
rm -f "${GROUP_COL_LIST}"

echo ""
echo "✅ Beta 多样性差异分析完成"
echo ""
echo "📊 输出文件:"
echo "   - unweighted_unifrac.svg/png: Unweighted UniFrac 差异箱线图"
echo "   - weighted_unifrac.svg/png: Weighted UniFrac 差异箱线图"
echo "   - beta_diff.svg/png: Beta 多样性差异合并图"
echo ""
