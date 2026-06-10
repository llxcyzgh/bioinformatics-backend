#!/bin/bash
# step3_upgma.sh - UPGMA 树构建脚本
# 用法：bash step3_upgma.sh -i <biom_table> -t <tree> -m <meta> -o <output_dir>

set -e

BIOM_TABLE=""
TREE_FILE=""
META_FILE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) BIOM_TABLE="$2"; shift 2 ;;
        -t|--tree) TREE_FILE="$2"; shift 2 ;;
        -m|--meta) META_FILE="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_upgma.sh -i <table> -t <tree> -m <meta> -o <output>"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${BIOM_TABLE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

mkdir -p "${OUTPUT_DIR}"/{UPGMA_sample,UPGMA_group}
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "UPGMA 树构建"
echo "=========================================="
echo ""

if [ -z "${TREE_FILE}" ] || [ -z "${META_FILE}" ]; then
    echo "⚠️  缺少必要文件，跳过 UPGMA 分析"
    exit 0
fi

echo "🌳 构建样本 UPGMA 树..."
source /gfs/users/guorongjun/miniconda3/bin/activate qiime1

jackknifed_beta_diversity.py \
    --otu_table_fp "${BIOM_TABLE}" \
    --force \
    --mapping_fp "${META_FILE}" \
    --tree_fp "${TREE_FILE}" \
    --output_dir UPGMA_sample \
    --seqs_per_sample 10000

echo "🌳 构建分组 UPGMA 树..."
if [ -f "group.mf" ]; then
    jackknifed_beta_diversity.py \
        --otu_table_fp "${BIOM_TABLE}" \
        --force \
        --mapping_fp group.mf \
        --tree_fp "${TREE_FILE}" \
        --output_dir UPGMA_group \
        --seqs_per_sample 10000
fi

echo ""
echo "✅ UPGMA 树构建完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - UPGMA_sample/unweighted_unifrac.png: 样本 Unweighted 树"
echo "   - UPGMA_group/unweighted_unifrac.png: 分组 Unweighted 树"
echo ""
