#!/bin/bash
# step4_ternary.sh - 三元相图分析脚本
# 用法：bash step4_ternary.sh -i <Relative_group/> -l <ternary.list>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
TERNARYPLOT_PL="${TERNARYPLOT_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/ternaryplot.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN TERNARYPLOT_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INDIR=""
TERNARY_LIST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INDIR="$2"; shift 2 ;;
        -l|--list) TERNARY_LIST="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_ternary.sh -i <Relative_group/> -l <ternary.list>"
            echo ""
            echo "参数:"
            echo "  -i, --input    分组相对丰度表目录路径"
            echo "  -l, --list     三元相图分组列表路径"
            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INDIR}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${TERNARY_LIST}" ] && { echo "❌ 错误：必须提供 -l"; exit 1; }
[ ! -d "${INDIR}" ] && { echo "❌ 错误：相对丰度表目录不存在：${INDIR}"; exit 1; }
[ ! -f "${TERNARY_LIST}" ] && { echo "❌ 错误：三元列表不存在：${TERNARY_LIST}"; exit 1; }

echo ""
echo "=========================================="
echo "三元相图分析"
echo "=========================================="
echo ""

echo "📊 分组相对丰度表目录：${INDIR}"
echo "📊 三元列表：${TERNARY_LIST}"
echo ""

# Step 1: 执行三元相图绘制
echo "[1/2] 绘制三元相图..."
"${PERL_BIN}" "${TERNARYPLOT_PL}" \
    "${INDIR}" \
    "${TERNARY_LIST}" \
    ./

# Step 2: SVG → PNG 转换（如果有 convert 命令）
if command -v convert &> /dev/null; then
    echo "[2/2] 转换 SVG → PNG..."
    for svg in *.svg; do
        if [ -f "${svg}" ]; then
            png="${svg%.svg}.png"
            convert -density 200 "${svg}" "${png}" 2>/dev/null || true
        fi
    done
else
    echo "⚠️  未找到 convert 命令，跳过 PNG 转换"
fi

echo ""
echo "✅ 三元相图分析完成"
echo ""
echo "📊 输出文件:"
echo "   - *.svg: 三元相图（SVG 格式）"
echo "   - *.png: 三元相图（PNG 格式）"
echo ""
