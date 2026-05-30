#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 05_dada2.sh
# 工具ID:   amp-dada2
# 功能说明: 使用DADA2进行ASV（Amplicon Sequence Variant）推断与去噪
#           对质控后的序列执行错误率学习、去噪、合并（双端）、去嵌合体
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/qc}"
OUTPUT_DIR="${2:-./results/dada2}"
TRUNC_LEN_F="${3:-0}"           # 正向序列截断位置 (0=不截断)
TRUNC_LEN_R="${4:-0}"           # 反向序列截断位置 (0=不截断)
MAX_EE_F="${5:-2}"              # 正向序列最大期望错误数
MAX_EE_R="${6:-2}"              # 反向序列最大期望错误数
CHIMERA_METHOD="${7:-consensus}" # 嵌合体检测方法: consensus/pooled/none
THREADS="${8:-4}"

# === 颜色输出 ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# === 参数校验 ===
INPUT_FILE="${INPUT_DIR}/qc-passed.qza"
if [[ ! -f "$INPUT_FILE" ]]; then
    log_error "未找到质控后的序列文件: $INPUT_FILE"
    log_error "请先运行 04_qc.sh 完成质量控制"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== DADA2 ASV推断参数 ==="
log_info "  正向截断长度: ${TRUNC_LEN_F} (0=不截断)"
log_info "  反向截断长度: ${TRUNC_LEN_R} (0=不截断)"
log_info "  正向最大期望错误: ${MAX_EE_F}"
log_info "  反向最大期望错误: ${MAX_EE_R}"
log_info "  嵌合体检测方法: ${CHIMERA_METHOD}"
log_info "  线程数: $THREADS"

# === 判断数据类型（单端/双端） ===
IS_PAIRED=false
if [[ -f "${INPUT_DIR}/demux-trimmed-rev.qza" ]]; then
    IS_PAIRED=true
    log_info "检测到双端数据模式"
fi

# === 执行DADA2去噪 ===
log_info "正在执行DADA2错误率学习与去噪..."
log_info "此步骤可能需要较长时间，取决于数据量大小"

if [[ "$IS_PAIRED" == "true" ]]; then
    # 双端DADA2去噪
    qiime dada2 denoise-paired \
        --i-demultiplexed-seqs "$INPUT_FILE" \
        --p-trunc-len-f "$TRUNC_LEN_F" \
        --p-trunc-len-r "$TRUNC_LEN_R" \
        --p-max-ee-f "$MAX_EE_F" \
        --p-max-ee-r "$MAX_EE_R" \
        --p-trim-left-f 0 \
        --p-trim-left-r 0 \
        --p-chimera-method "$CHIMERA_METHOD" \
        --p-n-threads "$THREADS" \
        --o-table "${OUTPUT_DIR}/asv-table.qza" \
        --o-representative-sequences "${OUTPUT_DIR}/rep-seqs.qza" \
        --o-denoising-stats "${OUTPUT_DIR}/denoise-stats.qza"
else
    # 单端DADA2去噪
    qiime dada2 denoise-single \
        --i-demultiplexed-seqs "$INPUT_FILE" \
        --p-trunc-len "$TRUNC_LEN_F" \
        --p-max-ee "$MAX_EE_F" \
        --p-trim-left 0 \
        --p-chimera-method "$CHIMERA_METHOD" \
        --p-n-threads "$THREADS" \
        --o-table "${OUTPUT_DIR}/asv-table.qza" \
        --o-representative-sequences "${OUTPUT_DIR}/rep-seqs.qza" \
        --o-denoising-stats "${OUTPUT_DIR}/denoise-stats.qza"
fi

if [[ $? -ne 0 ]]; then
    log_error "DADA2去噪失败，请检查输入数据质量和参数设置"
    exit 1
fi

# === 生成去噪统计可视化 ===
log_info "正在生成去噪统计报告..."
qiime metadata tabulate \
    --m-input-file "${OUTPUT_DIR}/denoise-stats.qza" \
    --o-visualization "${OUTPUT_DIR}/denoise-stats.qzv"

qiime feature-table summarize \
    --i-table "${OUTPUT_DIR}/asv-table.qza" \
    --o-visualization "${OUTPUT_DIR}/asv-table-summary.qzv"

qiime feature-table tabulate-seqs \
    --i-data "${OUTPUT_DIR}/rep-seqs.qza" \
    --o-visualization "${OUTPUT_DIR}/rep-seqs-summary.qzv"

log_info "DADA2 ASV推断完成！"
log_info "  ASV特征表: ${OUTPUT_DIR}/asv-table.qza"
log_info "  代表性序列: ${OUTPUT_DIR}/rep-seqs.qza"
log_info "  去噪统计: ${OUTPUT_DIR}/denoise-stats.qza"
log_info "  下一步: 运行 06_taxonomy.sh 进行物种分类注释"
