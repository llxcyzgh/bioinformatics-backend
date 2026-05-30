#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 04_qc.sh
# 工具ID:   amp-frags-qc
# 功能说明: 序列质量控制 - 包括质量过滤、长度筛选、去嵌合体
#           对拼接/单端序列进行质量筛选，去除低质量和异常序列
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./results/flash}"
OUTPUT_DIR="${2:-./results/qc}"
MIN_LENGTH="${3:-200}"          # 最小序列长度
MAX_LENGTH="${4:-1000}"         # 最大序列长度
MIN_QUALITY="${5:-20}"          # 最低平均质量分数
MAX_AMBIGUOUS="${6:-0}"         # 最大模糊碱基数 (N)
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
JOINED_FILE="${INPUT_DIR}/joined.qza"
if [[ ! -f "$JOINED_FILE" ]]; then
    log_error "未找到拼接后的序列文件: $JOINED_FILE"
    log_error "请先运行 03_flash.sh 完成双端拼接"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

log_info "=== 序列质量控制参数 ==="
log_info "  最小序列长度: ${MIN_LENGTH} bp"
log_info "  最大序列长度: ${MAX_LENGTH} bp"
log_info "  最低平均质量: Q${MIN_QUALITY}"
log_info "  最大模糊碱基: ${MAX_AMBIGUOUS}"
log_info "  线程数: $THREADS"

# === 第一步：质量过滤 ===
log_info "步骤 1/3: 执行质量过滤..."
qiime quality-filter q-score \
    --i-demux "$JOINED_FILE" \
    --p-min-quality "$MIN_QUALITY" \
    --p-quality-window 3 \
    --p-min-length-fraction 0.75 \
    --p-max-ambiguous "$MAX_AMBIGUOUS" \
    --o-filtered-sequences "${OUTPUT_DIR}/filtered.qza" \
    --o-filter-stats "${OUTPUT_DIR}/filter-stats.qza"

if [[ $? -ne 0 ]]; then
    log_error "质量过滤失败"
    exit 1
fi

# === 第二步：长度筛选 ===
log_info "步骤 2/3: 执行长度筛选..."
qiime feature-table filter-seqs \
    --i-data "${OUTPUT_DIR}/filtered.qza" \
    --p-min-length "$MIN_LENGTH" \
    --p-max-length "$MAX_LENGTH" \
    --o-filtered-data "${OUTPUT_DIR}/length-filtered.qza"

if [[ $? -ne 0 ]]; then
    log_error "长度筛选失败"
    exit 1
fi

# === 第三步：去嵌合体 ===
log_info "步骤 3/3: 去除嵌合体序列..."
qiime vsearch uchime-denovo \
    --i-sequences "${OUTPUT_DIR}/length-filtered.qza" \
    --o-chimeras "${OUTPUT_DIR}/chimeras.qza" \
    --o-nonchimeras "${OUTPUT_DIR}/nonchimeras.qza" \
    --o-stats "${OUTPUT_DIR}/chimera-stats.qza" \
    --p-threads "$THREADS"

if [[ $? -ne 0 ]]; then
    log_warn "去嵌合体步骤出现警告，继续后续分析..."
else
    log_info "嵌合体检测完成，使用非嵌合体序列继续分析"
    cp "${OUTPUT_DIR}/nonchimeras.qza" "${OUTPUT_DIR}/qc-passed.qza"
fi

# === 生成统计报告 ===
log_info "正在生成质量控制统计报告..."
qiime metadata tabulate \
    --m-input-file "${OUTPUT_DIR}/filter-stats.qza" \
    --o-visualization "${OUTPUT_DIR}/qc-stats.qzv"

log_info "序列质量控制完成！"
log_info "  质控通过序列: ${OUTPUT_DIR}/qc-passed.qza"
log_info "  过滤统计: ${OUTPUT_DIR}/filter-stats.qza"
log_info "  嵌合体统计: ${OUTPUT_DIR}/chimera-stats.qza"
log_info "  可视化报告: ${OUTPUT_DIR}/qc-stats.qzv"
log_info "  下一步: 运行 05_dada2.sh 进行ASV推断"
