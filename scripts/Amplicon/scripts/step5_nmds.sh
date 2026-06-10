#!/bin/bash
# step5_nmds.sh - NMDS 非度量多维尺度分析脚本
# 用法：bash step5_nmds.sh -t <asv_table.even.txt> -g <group.list> [-c <group_col.list>]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# Perl 脚本路径
NMDS_R_PL="${NMDS_R_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/NMDS/NMDS.R.pl}"

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

ASV_TABLE=""
GROUP_FILE=""
COLOR_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--table) ASV_TABLE="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -c|--color) COLOR_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step5_nmds.sh -t <asv_table.even.txt> -g <group.list> [-c <group_col.list>]"
            echo ""
            echo "参数:"
            echo "  -t, --table    均一化 ASV 表路径"
            echo "  -g, --group    样本分组文件路径"
            echo "  -c, --color    分组颜色配置文件路径（可选）"
            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${ASV_TABLE}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ ! -f "${ASV_TABLE}" ] && { echo "❌ 错误：ASV 表不存在：${ASV_TABLE}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

echo ""
echo "=========================================="
echo "NMDS 非度量多维尺度分析"
echo "=========================================="
echo ""

echo "📊 ASV 表：${ASV_TABLE}"
echo "📊 分组文件：${GROUP_FILE}"
if [ -n "${COLOR_FILE}" ] && [ -f "${COLOR_FILE}" ]; then
    echo "📊 颜色配置：${COLOR_FILE}"
fi
echo ""

# Step 1: 绘制 NMDS 排序图
echo "[1/2] 绘制 NMDS 排序图..."
"${PERL_BIN}" "${NMDS_R_PL}" "${ASV_TABLE}" "${GROUP_FILE}" "${COLOR_FILE:-${GROUP_FILE}}"

# Step 2: PDF → PNG 转换
echo "[2/2] 转换 PDF → PNG..."
"${CONVERT_BIN}" -density 300 NMDS.pdf NMDS.png 2>/dev/null || true

echo ""
echo "✅ NMDS 非度量多维尺度分析完成"
echo ""
echo "📊 输出文件:"
echo "   - NMDS.svg: NMDS 排序图（SVG 格式）"
echo "   - NMDS.pdf: NMDS 排序图（PDF 格式）"
echo "   - NMDS.png: NMDS 排序图（PNG 格式）"
echo ""
