#!/bin/bash
# step3_table_stats.sh - ASV 表均一化与相对丰度脚本
# 用法：bash step3_table_stats.sh -i <asv_table.txt>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN STAT_OTU_TAB_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

ASV_TABLE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) ASV_TABLE="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_table_stats.sh -i <asv_table.txt>"
            echo ""
            echo "参数:"
            echo "  -i, --input      ASV 表文件路径"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${ASV_TABLE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ ! -f "${ASV_TABLE}" ] && { echo "❌ 错误：ASV 表不存在：${ASV_TABLE}"; exit 1; }

echo ""
echo "=========================================="
echo "ASV 表均一化与相对丰度"
echo "=========================================="
echo ""

echo "📊 输入文件：${ASV_TABLE}"
echo ""

# Step 1: 数据均一化
echo "[1/2] 数据均一化..."
"${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
    "${ASV_TABLE}" \
    --even asv_table.even.txt \
    -unif min

# Step 2: 计算相对丰度
echo "[2/2] 计算相对丰度..."
mkdir -p Relative
"${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
    asv_table.even.txt \
    --prefix Relative/asv_table

echo ""
echo "✅ ASV 表均一化与相对丰度计算完成"
echo ""
echo "📊 输出文件:"
echo "   - asv_table.even.txt: 均一化 ASV 表"
echo "   - Relative/: 各层级相对丰度表 (k/p/c/o/f/g/s)"
echo ""
