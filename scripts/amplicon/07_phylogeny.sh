#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 07_phylogeny.sh
# 工具ID:   amp-phylogeny
# 功能说明: 基于ASV代表性序列构建系统发育树
#           包括多序列比对、系统发育树构建（FastTree/MAFFT）
#           用于后续Alpha/Beta多样性分析
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/dada2}"
OUTPUT_DIR="${2:-./results/phylogeny}"
ALIGN_METHOD="${3:-mafft}"       # 比对方法: mafft/clustal
TREE_METHOD="${4:-fasttree}"     # 建树方法: fasttree/iqtree/raxml
THREADS="${5:-4}"

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
if [[ ! -f "$REP_SEQS" ]]; then
    log_error "未找到ASV代表性序列: $REP_SEQS"
    log_error "请先运行 05_dada2.sh 完成ASV推断"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== 系统发育树构建参数 ==="
log_info "  序列比对方法: $ALIGN_METHOD"
log_info "  建树方法: $TREE_METHOD"
log_info "  线程数: $THREADS"

# === 方法一：QIIME2快速流程（推荐）===
# 使用 align-to-tree-mafft-fasttree pipeline 一步完成
log_info "正在使用快速流程构建系统发育树..."
log_info "此流程包含: 多序列比对 -> 位点过滤 -> 建树 -> 有根树"

qiime phylogeny align-to-tree-mafft-fasttree \
    --i-sequences "$REP_SEQS" \
    --p-n-threads "$THREADS" \
    --o-alignment "${OUTPUT_DIR}/aligned-rep-seqs.qza" \
    --o-masked-alignment "${OUTPUT_DIR}/masked-aligned-rep-seqs.qza" \
    --o-tree "${OUTPUT_DIR}/unrooted-tree.qza" \
    --o-rooted-tree "${OUTPUT_DIR}/rooted-tree.qza"

if [[ $? -ne 0 ]]; then
    log_warn "快速流程失败，尝试逐步执行..."

    # === 方法二：逐步执行 ===
    log_info "步骤 1/4: 执行多序列比对 (MAFFT)..."
    qiime mafft align \
        --i-sequences "$REP_SEQS" \
        --p-n-threads "$THREADS" \
        --o-alignment "${OUTPUT_DIR}/aligned-rep-seqs.qza"

    log_info "步骤 2/4: 过滤比对位点（去除高变区）..."
    qiime alignment mask \
        --i-alignment "${OUTPUT_DIR}/aligned-rep-seqs.qza" \
        --o-masked-alignment "${OUTPUT_DIR}/masked-aligned-rep-seqs.qza"

    log_info "步骤 3/4: 构建无根系统发育树 (FastTree)..."
    qiime fasttree \
        --i-alignment "${OUTPUT_DIR}/masked-aligned-rep-seqs.qza" \
        --p-n-threads "$THREADS" \
        --o-tree "${OUTPUT_DIR}/unrooted-tree.qza"

    log_info "步骤 4/4: 构建有根系统发育树（中点生根法）..."
    qiime phylogeny midpoint-root \
        --i-tree "${OUTPUT_DIR}/unrooted-tree.qza" \
        --o-rooted-tree "${OUTPUT_DIR}/rooted-tree.qza"
fi

# === 验证输出文件 ===
FILES_OK=true
for f in aligned-rep-seqs.qza masked-aligned-rep-seqs.qza unrooted-tree.qza rooted-tree.qza; do
    if [[ ! -f "${OUTPUT_DIR}/${f}" ]]; then
        log_error "缺失输出文件: ${OUTPUT_DIR}/${f}"
        FILES_OK=false
    fi
done

if [[ "$FILES_OK" == "true" ]]; then
    log_info "系统发育树构建完成！"
    log_info "  多序列比对: ${OUTPUT_DIR}/aligned-rep-seqs.qza"
    log_info "  过滤后比对: ${OUTPUT_DIR}/masked-aligned-rep-seqs.qza"
    log_info "  无根树: ${OUTPUT_DIR}/unrooted-tree.qza"
    log_info "  有根树: ${OUTPUT_DIR}/rooted-tree.qza"
    log_info "  下一步: 运行 08_feature_tables.sh 构建特征表"
else
    log_error "系统发育树构建不完整，请检查上方错误信息"
    exit 1
fi
