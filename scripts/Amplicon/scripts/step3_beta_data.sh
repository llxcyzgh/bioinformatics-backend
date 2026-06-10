#!/bin/bash
# step3_beta_data.sh - Beta 多样性分析脚本
# 用法：bash step3_beta_data.sh -i <even_table> -t <tree> -m <meta> -o <output_dir>

set -e

EVEN_TABLE=""
TREE_FILE=""
META_FILE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) EVEN_TABLE="$2"; shift 2 ;;
        -t|--tree) TREE_FILE="$2"; shift 2 ;;
        -m|--meta) META_FILE="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_beta_data.sh -i <table> -t <tree> -m <meta> -o <output>"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${EVEN_TABLE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "Beta 多样性分析"
echo "=========================================="
echo ""

if [ -z "${TREE_FILE}" ] || [ -z "${META_FILE}" ]; then
    echo "⚠️  缺少树文件或元数据，跳过 Beta 多样性分析"
    exit 0
fi

echo "🔬 执行 Beta 多样性核心分析..."
source /software/anaconda3/bin/activate 16s-env

qiime diversity core-metrics-phylogenetic \
    --i-phylogeny "${TREE_FILE}" \
    --i-table "${EVEN_TABLE}" \
    --p-sampling-depth 10000 \
    --m-metadata-file "${META_FILE}" \
    --p-n-jobs-or-threads 3 \
    --o-rarefied-table rarefied_table.qza \
    --o-unweighted-unifrac-distance-matrix unweighted_unifrac_distance_matrix.qza \
    --o-weighted-unifrac-distance-matrix weighted_unifrac_distance_matrix.qza \
    --o-jaccard-distance-matrix jaccard_distance_matrix.qza \
    --o-bray-curtis-distance-matrix bray_curtis_distance_matrix.qza \
    --o-unweighted-unifrac-pcoa-results unweighted_unifrac_pcoa_results.qza \
    --o-weighted-unifrac-pcoa-results weighted_unifrac_pcoa_results.qza \
    --o-unweighted-unifrac-emperor unweighted_unifrac_emperor.qzv \
    --o-weighted-unifrac-emperor weighted_unifrac_emperor.qzv

echo ""
echo "✅ Beta 多样性分析完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - *_emperor.qzv: Emperor 交互式可视化"
echo "   - *_distance_matrix.qza: 距离矩阵"
echo ""
