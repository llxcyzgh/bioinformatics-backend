#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 03_flash.sh
# 工具ID:   amp-flash
# 功能说明: 使用FLASH工具进行双端序列拼接（merge paired-end reads）
#           将R1和R2配对序列合并为一条完整的重叠群序列
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/cutadapt}"
OUTPUT_DIR="${2:-./results/flash}"
MIN_OVERLAP="${3:-10}"          # 最小重叠长度
MAX_OVERLAP="${4:-250}"         # 最大重叠长度
MAX_MISMATCH_DENSITY="${5:-0.25}" # 重叠区最大错配密度
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
if [[ ! -d "$INPUT_DIR" ]]; then
    log_error "输入目录不存在: $INPUT_DIR"
    log_error "请先运行 02_cutadapt.sh 完成引物切除"
    exit 1
fi

FWD_FILE="${INPUT_DIR}/demux-trimmed-fwd.qza"
REV_FILE="${INPUT_DIR}/demux-trimmed-rev.qza"

if [[ ! -f "$FWD_FILE" ]]; then
    log_error "未找到正向序列文件: $FWD_FILE"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== FLASH 双端拼接参数 ==="
log_info "  最小重叠长度: ${MIN_OVERLAP} bp"
log_info "  最大重叠长度: ${MAX_OVERLAP} bp"
log_info "  最大错配密度: ${MAX_MISMATCH_DENSITY}"
log_info "  线程数: $THREADS"

# === 检查是否为双端数据 ===
if [[ -f "$REV_FILE" ]]; then
    log_info "检测到双端测序数据，开始拼接..."

    # 使用QIIME2的VSEARCH插件进行双端拼接（QIIME2原生支持）
    qiime vsearch join-pairs \
        --i-demultiplexed-seqs "${INPUT_DIR}/demux-trimmed-fwd.qza" \
        --p-minovlength "$MIN_OVERLAP" \
        --p-maxdiffs $(( $(echo "$MAX_OVERLAP" | awk '{print int($1 * 0.25)}') )) \
        --p-allowmergestagger \
        --p-threads "$THREADS" \
        --o-joined-seqs "${OUTPUT_DIR}/joined.qza"

    if [[ $? -ne 0 ]]; then
        log_warn "VSEARCH拼接失败，尝试使用fastq-join方法..."
        # 备选方案：使用fastq-join
        qiime fastq-join join-pairs \
            --i-demultiplexed-seqs "${INPUT_DIR}/demux-trimmed-fwd.qza" \
            --p-min-overlap "$MIN_OVERLAP" \
            --p-max-mismatch-density "$MAX_MISMATCH_DENSITY" \
            --o-joined-seqs "${OUTPUT_DIR}/joined.qza"
    fi
else
    log_warn "未检测到反向序列文件，跳过双端拼接"
    log_info "直接复制单端数据作为拼接结果..."
    cp "$FWD_FILE" "${OUTPUT_DIR}/joined.qza"
fi

# === 拼接质量统计 ===
log_info "正在生成拼接统计摘要..."
qiime demux summarize \
    --i-data "${OUTPUT_DIR}/joined.qza" \
    --o-visualization "${OUTPUT_DIR}/joined-summary.qzv"

# === 输出拼接统计信息 ===
log_info "双端序列拼接完成！"
log_info "  拼接后数据: ${OUTPUT_DIR}/joined.qza"
log_info "  可视化摘要: ${OUTPUT_DIR}/joined-summary.qzv"
log_info "  下一步: 运行 04_qc.sh 进行序列质量控制"
