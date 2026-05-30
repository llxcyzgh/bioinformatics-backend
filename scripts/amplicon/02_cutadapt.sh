#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 02_cutadapt.sh
# 工具ID:   amp-cutadapt
# 功能说明: 使用Cutadapt切除扩增子测序数据中的引物和接头序列
#           支持双端引物切除，可处理简并碱基
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/qiime2}"
OUTPUT_DIR="${2:-./results/cutadapt}"
FORWARD_PRIMER="${3:-AGRGTTTGATCMTGGCTCAG}"    # 16S通用正向引物 (27F简并)
REVERSE_PRIMER="${4:-RGYTACCTTGTTACGACTT}"      # 16S通用反向引物 (1492R简并)
MIN_LENGTH="${5:-100}"                           # 切除后最小序列长度
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
if [[ ! -f "${INPUT_DIR}/demux.qza" ]]; then
    log_error "未找到导入的序列文件: ${INPUT_DIR}/demux.qza"
    log_error "请先运行 01_import_fasta.sh 完成数据导入"
    exit 1
fi

if [[ -z "$FORWARD_PRIMER" ]] || [[ -z "$REVERSE_PRIMER" ]]; then
    log_error "正向引物和反向引物不能为空"
    log_error "用法: $0 <输入目录> <输出目录> <正向引物> <反向引物> [最短长度] [线程数]"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== Cutadapt 引物切除参数 ==="
log_info "  正向引物 (5'-3'): $FORWARD_PRIMER"
log_info "  反向引物 (5'-3'): $REVERSE_PRIMER"
log_info "  最短保留长度: $MIN_LENGTH bp"
log_info "  线程数: $THREADS"

# === 计算引物长度用于误差容忍度 ===
FWD_LEN=${#FORWARD_PRIMER}
REV_LEN=${#REVERSE_PRIMER}
FWD_ERROR=$((FWD_LEN / 10 + 1))   # 允许10%错配
REV_ERROR=$((REV_LEN / 10 + 1))

log_info "  正向引物长度: ${FWD_LEN}bp, 允许错配: ${FWD_ERROR}"
log_info "  反向引物长度: ${REV_LEN}bp, 允许错配: ${REV_ERROR}"

# === 正向序列引物切除 ===
log_info "正在切除正向序列中的引物..."
qiime cutadapt trim-single \
    --i-demultiplexed-sequences "${INPUT_DIR}/demux.qza" \
    --p-front "$FORWARD_PRIMER" \
    --p-adapter "$REVERSE_PRIMER" \
    --p-error-rate 0.1 \
    --p-minimum-length "$MIN_LENGTH" \
    --p-cores "$THREADS" \
    --o-trimmed-sequences "${OUTPUT_DIR}/demux-trimmed-fwd.qza"

if [[ $? -ne 0 ]]; then
    log_error "正向序列引物切除失败"
    exit 1
fi

# === 反向序列引物切除（双端数据） ===
if [[ -f "${INPUT_DIR}/demux-rev.qza" ]]; then
    log_info "检测到双端数据，正在切除反向序列中的引物..."
    qiime cutadapt trim-single \
        --i-demultiplexed-sequences "${INPUT_DIR}/demux-rev.qza" \
        --p-front "$REVERSE_PRIMER" \
        --p-adapter "$FORWARD_PRIMER" \
        --p-error-rate 0.1 \
        --p-minimum-length "$MIN_LENGTH" \
        --p-cores "$THREADS" \
        --o-trimmed-sequences "${OUTPUT_DIR}/demux-trimmed-rev.qza"
fi

# === 生成切除后的统计摘要 ===
log_info "正在生成切除统计摘要..."
qiime demux summarize \
    --i-data "${OUTPUT_DIR}/demux-trimmed-fwd.qza" \
    --o-visualization "${OUTPUT_DIR}/trimmed-summary.qzv"

log_info "引物切除完成！"
log_info "  切除后数据: ${OUTPUT_DIR}/demux-trimmed-fwd.qza"
log_info "  可视化摘要: ${OUTPUT_DIR}/trimmed-summary.qzv"
