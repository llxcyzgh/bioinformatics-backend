#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 08_feature_tables.sh
# 工具ID:   amp-feature-tables
# 功能说明: ASV特征表构建与处理
#           包括过滤低丰度ASV、去除线粒体/叶绿体序列、合并样本
#           生成最终用于下游分析的特征表
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/dada2}"
TAXONOMY_DIR="${2:-./results/taxonomy}"
METADATA_FILE="${3:-./data/metadata.tsv}"
OUTPUT_DIR="${4:-./results/feature-tables}"
MIN_FREQUENCY="${5:-10}"         # ASV最小出现频次
MIN_SAMPLES="${6:-2}"            # ASV至少出现在多少个样本中
SAMPLE_MAX_FREQ="${7:-0}"        # 样本最大频率阈值 (0=不限制)
EXCLUDE_MITO="${8:-true}"        # 排除线粒体序列
EXCLUDE_CHLORO="${9:-true}"      # 排除叶绿体序列

# === 颜色输出 ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# === 参数校验 ===
ASV_TABLE="${INPUT_DIR}/asv-table.qza"
TAXONOMY="${TAXONOMY_DIR}/taxonomy.qza"

if [[ ! -f "$ASV_TABLE" ]]; then
    log_error "未找到ASV特征表: $ASV_TABLE"
    log_error "请先运行 05_dada2.sh"
    exit 1
fi

if [[ ! -f "$TAXONOMY" ]]; then
    log_error "未找到物种分类文件: $TAXONOMY"
    log_error "请先运行 06_taxonomy.sh"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== ASV特征表构建参数 ==="
log_info "  ASV最小频次: ${MIN_FREQUENCY}"
log_info "  最少出现样本数: ${MIN_SAMPLES}"
log_info "  排除线粒体: $EXCLUDE_MITO"
log_info "  排除叶绿体: $EXCLUDE_CHLORO"

# === 第一步：基于频率和样本数过滤 ===
log_info "步骤 1/4: 过滤低丰度ASV..."
qiime feature-table filter-features \
    --i-table "$ASV_TABLE" \
    --p-min-frequency "$MIN_FREQUENCY" \
    --p-min-samples "$MIN_SAMPLES" \
    --o-filtered-table "${OUTPUT_DIR}/table-filtered.qza"

# === 第二步：排除线粒体和叶绿体序列 ===
log_info "步骤 2/4: 排除非目标序列（线粒体/叶绿体）..."

# 构建排除关键词列表
EXCLUDE_TERMS=""
if [[ "$EXCLUDE_MITO" == "true" ]]; then
    EXCLUDE_TERMS="mitochondria"
    log_info "  排除线粒体序列"
fi

if [[ "$EXCLUDE_CHLORO" == "true" ]]; then
    if [[ -n "$EXCLUDE_TERMS" ]]; then
        EXCLUDE_TERMS="${EXCLUDE_TERMS},chloroplast"
    else
        EXCLUDE_TERMS="chloroplast"
    fi
    log_info "  排除叶绿体序列"
fi

if [[ -n "$EXCLUDE_TERMS" ]]; then
    qiime taxa filter-table \
        --i-table "${OUTPUT_DIR}/table-filtered.qza" \
        --i-taxonomy "$TAXONOMY" \
        --p-exclude "$EXCLUDE_TERMS" \
        --p-mode contains \
        --o-filtered-table "${OUTPUT_DIR}/table-no-contam.qza"
else
    cp "${OUTPUT_DIR}/table-filtered.qza" "${OUTPUT_DIR}/table-no-contam.qza"
fi

# === 第三步：基于元数据过滤样本（如提供）===
log_info "步骤 3/4: 样本筛选..."
if [[ -f "$METADATA_FILE" ]] && [[ "$METADATA_FILE" != "./data/metadata.tsv" ]]; then
    qiime feature-table filter-samples \
        --i-table "${OUTPUT_DIR}/table-no-contam.qza" \
        --m-metadata-file "$METADATA_FILE" \
        --o-filtered-table "${OUTPUT_DIR}/table-sampled.qza"
    log_info "  使用元数据文件过滤样本: $METADATA_FILE"
else
    cp "${OUTPUT_DIR}/table-no-contam.qza" "${OUTPUT_DIR}/table-sampled.qza"
    log_warn "  未提供元数据文件，跳过样本过滤"
fi

# === 第四步：生成最终特征表摘要 ===
log_info "步骤 4/4: 生成最终特征表摘要..."
cp "${OUTPUT_DIR}/table-sampled.qza" "${OUTPUT_DIR}/final-table.qza"

qiime feature-table summarize \
    --i-table "${OUTPUT_DIR}/final-table.qza" \
    --m-sample-metadata-file "$METADATA_FILE" \
    --o-visualization "${OUTPUT_DIR}/final-table-summary.qzv" 2>/dev/null || \
qiime feature-table summarize \
    --i-table "${OUTPUT_DIR}/final-table.qza" \
    --o-visualization "${OUTPUT_DIR}/final-table-summary.qzv"

log_info "ASV特征表构建完成！"
log_info "  最终特征表: ${OUTPUT_DIR}/final-table.qza"
log_info "  可视化摘要: ${OUTPUT_DIR}/final-table-summary.qzv"
log_info "  下一步: 运行 09_table_stats.sh 进行均一化与丰度计算"
