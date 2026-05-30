#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 09_table_stats.sh
# 工具ID:   amp-table-stats
# 功能说明: ASV特征表均一化与丰度统计计算
#           包括抽平(rarefaction)、Alpha多样性、Beta多样性计算
#           生成物种丰度矩阵和多样性分析结果
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/feature-tables}"
PHYLO_DIR="${2:-./results/phylogeny}"
TAXONOMY_DIR="${3:-./results/taxonomy}"
METADATA_FILE="${4:-./data/metadata.tsv}"
OUTPUT_DIR="${5:-./results/stats}"
RAREFACTION_DEPTH="${6:-auto}"  # 抽平深度 (auto=自动计算最小样本量的90%)
THREADS="${7:-4}"

# === 颜色输出 ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# === 参数校验 ===
FINAL_TABLE="${INPUT_DIR}/final-table.qza"
ROOTED_TREE="${PHYLO_DIR}/rooted-tree.qza"
TAXONOMY="${TAXONOMY_DIR}/taxonomy.qza"

for f in "$FINAL_TABLE" "$ROOTED_TREE" "$TAXONOMY"; do
    if [[ ! -f "$f" ]]; then
        log_error "缺失必要文件: $f"
        exit 1
    fi
done

mkdir -p "$OUTPUT_DIR"

# === 确定抽平深度 ===
if [[ "$RAREFACTION_DEPTH" == "auto" ]]; then
    log_info "自动计算抽平深度..."
    # 导出特征表并计算每个样本的序列数
    qiime feature-table summarize \
        --i-table "$FINAL_TABLE" \
        --o-visualization "${OUTPUT_DIR}/pre-rarefaction-summary.qzv"

    # 使用QIIME2计算最小样本频率
    MIN_DEPTH=$(qiime feature-table stats \
        --i-table "$FINAL_TABLE" \
        --o-sample-summary "${OUTPUT_DIR}/sample-stats.qza" 2>/dev/null | \
        grep -oP 'Minimum frequency: \K\d+' || echo "")

    if [[ -z "$MIN_DEPTH" ]]; then
        RAREFACTION_DEPTH=1000
        log_warn "无法自动计算抽平深度，使用默认值: $RAREFACTION_DEPTH"
    else
        RAREFACTION_DEPTH=$((MIN_DEPTH * 90 / 100))
        log_info "最小样本序列数: ${MIN_DEPTH}，抽平深度设为90%: ${RAREFACTION_DEPTH}"
    fi
fi

log_info "=== 均一化与统计参数 ==="
log_info "  抽平深度: ${RAREFACTION_DEPTH}"
log_info "  线程数: $THREADS"

# === 第一步：抽平（Rarefaction） ===
log_info "步骤 1/4: 执行序列数抽平（Rarefaction）..."
qiime feature-table rarefy \
    --i-table "$FINAL_TABLE" \
    --p-sampling-depth "$RAREFACTION_DEPTH" \
    --o-rarefied-table "${OUTPUT_DIR}/rarefied-table.qza"

if [[ $? -ne 0 ]]; then
    log_error "抽平失败，请检查抽平深度是否大于最小样本序列数"
    exit 1
fi

# === 第二步：Alpha多样性分析 ===
log_info "步骤 2/4: 计算Alpha多样性指数..."
qiime diversity alpha \
    --i-table "${OUTPUT_DIR}/rarefied-table.qza" \
    --p-metric shannon \
    --o-alpha-diversity "${OUTPUT_DIR}/alpha-shannon.qza"

qiime diversity alpha \
    --i-table "${OUTPUT_DIR}/rarefied-table.qza" \
    --p-metric observed_features \
    --o-alpha-diversity "${OUTPUT_DIR}/alpha-observed.qza"

qiime diversity alpha-phylogenetic \
    --i-table "${OUTPUT_DIR}/rarefied-table.qza" \
    --i-phylogeny "$ROOTED_TREE" \
    --p-metric faith_pd \
    --o-alpha-diversity "${OUTPUT_DIR}/alpha-faith-pd.qza"

log_info "  Shannon指数: ${OUTPUT_DIR}/alpha-shannon.qza"
log_info "  Observed ASVs: ${OUTPUT_DIR}/alpha-observed.qza"
log_info "  Faith PD: ${OUTPUT_DIR}/alpha-faith-pd.qza"

# === 第三步：Beta多样性分析 ===
log_info "步骤 3/4: 计算Beta多样性距离矩阵..."
qiime diversity beta \
    --i-table "${OUTPUT_DIR}/rarefied-table.qza" \
    --p-metric braycurtis \
    --o-distance-matrix "${OUTPUT_DIR}/beta-braycurtis.qza"

qiime diversity beta-phylogenetic \
    --i-table "${OUTPUT_DIR}/rarefied-table.qza" \
    --i-phylogeny "$ROOTED_TREE" \
    --p-metric weighted_unifrac \
    --o-distance-matrix "${OUTPUT_DIR}/beta-weighted-unifrac.qza"

qiime diversity beta-phylogenetic \
    --i-table "${OUTPUT_DIR}/rarefied-table.qza" \
    --i-phylogeny "$ROOTED_TREE" \
    --p-metric unweighted_unifrac \
    --o-distance-matrix "${OUTPUT_DIR}/beta-unweighted-unifrac.qza"

log_info "  Bray-Curtis: ${OUTPUT_DIR}/beta-braycurtis.qza"
log_info "  Weighted UniFrac: ${OUTPUT_DIR}/beta-weighted-unifrac.qza"
log_info "  Unweighted UniFrac: ${OUTPUT_DIR}/beta-unweighted-unifrac.qza"

# === 第四步：生成相对丰度表 ===
log_info "步骤 4/4: 计算相对丰度..."
qiime feature-table relative-frequency \
    --i-table "${OUTPUT_DIR}/rarefied-table.qza" \
    --o-relative-frequency-table "${OUTPUT_DIR}/relative-abundance.qza"

# === 最终统计汇总 ===
log_info "=========================================="
log_info "  ASV表均一化与丰度统计全部完成！"
log_info "=========================================="
log_info "  抽平后特征表: ${OUTPUT_DIR}/rarefied-table.qza"
log_info "  相对丰度表: ${OUTPUT_DIR}/relative-abundance.qza"
log_info "  Alpha多样性: ${OUTPUT_DIR}/alpha-*.qza"
log_info "  Beta多样性: ${OUTPUT_DIR}/beta-*.qza"
log_info ""
log_info "分析流程至此全部完成，结果可用于后续统计检验与可视化。"
