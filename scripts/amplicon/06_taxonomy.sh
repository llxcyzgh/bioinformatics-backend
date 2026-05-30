#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 06_taxonomy.sh
# 工具ID:   amp-taxonomy
# 功能说明: 对ASV代表性序列进行物种分类注释
#           支持多数据库：Silva/Greengenes/UNITE，使用Naive Bayes分类器
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/dada2}"
OUTPUT_DIR="${2:-./results/taxonomy}"
CLASSIFIER="${3:-./refs/silva-138-99-515-806-nb-classifier.qza}"  # 分类器文件
DATABASE="${4:-silva}"            # 数据库名称: silva/greengenes/unite
CONFIDENCE="${5:-0.7}"            # 分类置信度阈值
THREADS="${6:-4}"

# === 颜色输出 ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# === 参数校验 ===
REP_SEQS="${INPUT_DIR}/rep-seqs.qza"
ASV_TABLE="${INPUT_DIR}/asv-table.qza"

if [[ ! -f "$REP_SEQS" ]]; then
    log_error "未找到ASV代表性序列: $REP_SEQS"
    log_error "请先运行 05_dada2.sh 完成ASV推断"
    exit 1
fi

if [[ ! -f "$CLASSIFIER" ]]; then
    log_error "未找到分类器文件: $CLASSIFIER"
    log_error "请下载预训练分类器或指定正确路径"
    log_error ""
    log_error "常用分类器下载地址:"
    log_error "  Silva-138:   https://data.qiime2.org/classifiers/silva-138-99-515-806-nb-classifier.qza"
    log_error "  Greengenes:  https://data.qiime2.org/classifiers/gg-13-8-99-515-806-nb-classifier.qza"
    log_error "  UNITE (真菌): https://data.qiime2.org/classifiers/unite-ver8-dynamic-classifier.qza"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== 物种分类注释参数 ==="
log_info "  分类数据库: $DATABASE"
log_info "  分类器文件: $CLASSIFIER"
log_info "  置信度阈值: $CONFIDENCE"
log_info "  线程数: $THREADS"

# === 执行物种分类 ===
log_info "正在执行物种分类注释..."
log_info "使用 ${DATABASE} 数据库 Naive Bayes 分类器"

qiime feature-classifier classify-sklearn \
    --i-classifier "$CLASSIFIER" \
    --i-reads "$REP_SEQS" \
    --p-confidence "$CONFIDENCE" \
    --p-n-jobs "$THREADS" \
    --o-classification "${OUTPUT_DIR}/taxonomy.qza"

if [[ $? -ne 0 ]]; then
    log_error "物种分类注释失败，请检查分类器文件是否与序列匹配"
    exit 1
fi

# === 生成分类结果可视化 ===
log_info "正在生成分类结果报告..."
qiime metadata tabulate \
    --m-input-file "${OUTPUT_DIR}/taxonomy.qza" \
    --o-visualization "${OUTPUT_DIR}/taxonomy.qzv"

# === 按分类层级过滤特征表（可选）===
log_info "正在生成各分类层级的特征表..."
qiime taxa collapse \
    --i-table "$ASV_TABLE" \
    --i-taxonomy "${OUTPUT_DIR}/taxonomy.qza" \
    --p-level 2 \
    --o-collapsed-table "${OUTPUT_DIR}/table-l2.qza"

qiime taxa collapse \
    --i-table "$ASV_TABLE" \
    --i-taxonomy "${OUTPUT_DIR}/taxonomy.qza" \
    --p-level 6 \
    --o-collapsed-table "${OUTPUT_DIR}/table-l6.qza"

qiime taxa collapse \
    --i-table "$ASV_TABLE" \
    --i-taxonomy "${OUTPUT_DIR}/taxonomy.qza" \
    --p-level 7 \
    --o-collapsed-table "${OUTPUT_DIR}/table-l7.qza"

# === 分类柱状图 ===
qiime taxa barplot \
    --i-table "$ASV_TABLE" \
    --i-taxonomy "${OUTPUT_DIR}/taxonomy.qza" \
    --o-visualization "${OUTPUT_DIR}/taxa-barplot.qzv"

log_info "物种分类注释完成！"
log_info "  分类结果: ${OUTPUT_DIR}/taxonomy.qza"
log_info "  门水平 (L2): ${OUTPUT_DIR}/table-l2.qza"
log_info "  属水平 (L6): ${OUTPUT_DIR}/table-l6.qza"
log_info "  种水平 (L7): ${OUTPUT_DIR}/table-l7.qza"
log_info "  分类柱状图: ${OUTPUT_DIR}/taxa-barplot.qzv"
log_info "  下一步: 运行 07_phylogeny.sh 构建系统发育树"
