#!/bin/bash
# step4_krona.sh - Krona 交互式物种组成可视化脚本
# 用法：bash step4_krona.sh -t <asv_table.even.txt> [-o <output_dir>]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
IMPORT_RDP_PL="${IMPORT_RDP_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Krona/ImportRDP.pl}"
KRONA_LIB="${KRONA_LIB:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Krona}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN IMPORT_RDP_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

ASV_TABLE=""
OUTPUT_NAME="krona"

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--table) ASV_TABLE="$2"; shift 2 ;;
        -o|--output) OUTPUT_NAME="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_krona.sh -t <asv_table.even.txt> [-o <output_dir>]"
            echo ""
            echo "参数:"
            echo "  -t, --table    均一化 ASV 表路径"
            echo "  -o, --output   输出目录名称（默认：krona）"
            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${ASV_TABLE}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ ! -f "${ASV_TABLE}" ] && { echo "❌ 错误：ASV 表不存在：${ASV_TABLE}"; exit 1; }

echo ""
echo "=========================================="
echo "Krona 交互式物种组成可视化"
echo "=========================================="
echo ""

echo "📊 输入文件：${ASV_TABLE}"
echo "📊 输出目录：${OUTPUT_NAME}"
echo ""

# Step 1: 生成 krona.html
echo "[1/2] 生成 Krona 交互式图表..."
"${PERL_BIN}" "${IMPORT_RDP_PL}" \
    "${ASV_TABLE}" \
    -o krona.html \
    -n root \
    -u ./

# Step 2: 复制资源文件
echo "[2/2] 复制资源文件..."
cp -rf "${KRONA_LIB}"/{img,src} ./

echo ""
echo "✅ Krona 交互式图表生成完成"
echo ""
echo "📊 输出文件:"
echo "   - krona.html: Krona 交互式图表（用浏览器打开）"
echo "   - img/: Krona 图片资源"
echo "   - src/: Krona JavaScript 源码"
echo ""
echo "💡 使用方法：用浏览器打开 krona.html 查看交互式图表"
echo ""
