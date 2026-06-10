#!/bin/bash
# step4_venn.sh - 维恩图分析脚本
# 用法：bash step4_venn.sh -t <table> -l <venn_list> -o <output_dir>

set -e

TABLE_FILE=""
VENN_LIST=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--table) TABLE_FILE="$2"; shift 2 ;;
        -l|--list) VENN_LIST="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_venn.sh -t <table> -l <list> -o <output>"
            echo ""
            echo "参数:"
            echo "  -t, --table      分组 ASV 表"
            echo "  -l, --list       维恩图分组列表"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${TABLE_FILE}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${VENN_LIST}" ] && { echo "❌ 错误：必须提供 -l"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
[ ! -f "${TABLE_FILE}" ] && { echo "❌ 错误：ASV 表不存在"; exit 1; }
[ ! -f "${VENN_LIST}" ] && { echo "❌ 错误：维恩图列表不存在"; exit 1; }

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "维恩图分析"
echo "=========================================="
echo ""

echo "🎨 绘制维恩图..."
perl /newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/venn.pl \
    "${TABLE_FILE}" "${VENN_LIST}" > Venn_group.log

echo "✅ 维恩图绘制完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - *.svg/png: 维恩图图片"
echo "   - *.xls: 维恩图数据表"
echo ""
