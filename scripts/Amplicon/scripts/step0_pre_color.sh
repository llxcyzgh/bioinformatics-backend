#!/bin/bash
# step0_pre_color.sh - 分组颜色配置文件生成脚本
# 用法：bash step0_pre_color.sh -i <group> -o <output>

set -e

GROUP=""
OUTPUT=""
SCRIPT_PATH="/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--group) GROUP="$2"; shift 2 ;;
        -o|--output) OUTPUT="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step0_pre_color.sh -i <group> -o <output>"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${GROUP}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${OUTPUT}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

echo ""
echo "=========================================="
echo "分组颜色配置文件生成"
echo "=========================================="
echo ""

echo "🎨 执行 color_defined.pl..."
perl "${SCRIPT_PATH}" "${GROUP}" "${OUTPUT}"

echo "✅ 分组颜色配置文件生成完成"
echo ""
echo "📁 输入：${GROUP}"
echo "📁 输出：${OUTPUT}"
echo "📊 文件格式：三列 TSV (样本 ID、分组名、颜色代码)"
echo ""
