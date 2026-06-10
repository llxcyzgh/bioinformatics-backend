#!/bin/bash
# step3_feature_tables.sh - ASV 特征表构建脚本
# 用法：bash step3_feature_tables.sh -i <featureTable.biom> -t <all_tax_assignments.txt>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
CONDA_BIN="${CONDA_BIN:-/software/anaconda3/bin/conda}"
BIOM_BIN="${BIOM_BIN:-/software/anaconda3/envs/16s-env/bin/biom}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in CONDA_BIN BIOM_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

BIOM_TABLE=""
TAXONOMY=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) BIOM_TABLE="$2"; shift 2 ;;
        -t|--taxonomy) TAXONOMY="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_feature_tables.sh -i <featureTable.biom> -t <all_tax_assignments.txt>"
            echo ""
            echo "参数:"
            echo "  -i, --input      BIOM 格式特征表路径"
            echo "  -t, --taxonomy   物种注释文件路径"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${BIOM_TABLE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${TAXONOMY}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ ! -f "${BIOM_TABLE}" ] && { echo "❌ 错误：BIOM 表不存在：${BIOM_TABLE}"; exit 1; }
[ ! -f "${TAXONOMY}" ] && { echo "❌ 错误：物种注释文件不存在：${TAXONOMY}"; exit 1; }

echo ""
echo "=========================================="
echo "ASV 特征表构建"
echo "=========================================="
echo ""

echo "🔧 添加物种注释到特征表..."
echo "   BIOM 表：${BIOM_TABLE}"
echo "   物种注释：${TAXONOMY}"

# 激活 conda 环境
source "${CONDA_BIN}/activate" 16s-env

# Step 1: 添加物种注释到 BIOM 表
"${BIOM_BIN}" add-metadata \
    -i "${BIOM_TABLE}" \
    -o featureTaxonomy.biom \
    --observation-metadata-fp "${TAXONOMY}" \
    --sc-separated taxonomy

# Step 2: BIOM → TSV 转换
echo "🔄 BIOM → TSV 转换..."
"${BIOM_BIN}" convert \
    -i featureTaxonomy.biom \
    -o asv_table.txt \
    --to-tsv \
    --header-key taxonomy

# Step 3: 格式标准化
echo "📝 标准化格式..."
sed -i '1d' asv_table.txt
sed -i '1s/taxonomy/Taxonomy/g' asv_table.txt
sed -i '1s/OTU ID/OTU_num/g' asv_table.txt
sed -i 's/; /;/g' asv_table.txt

echo ""
echo "✅ ASV 特征表构建完成"
echo ""
echo "📊 输出文件:"
echo "   - asv_table.txt: 标准化 ASV 特征表"
echo "   - featureTaxonomy.biom: 带物种注释的 BIOM 表"
echo ""
