#!/bin/bash
set -euo pipefail

# ==============================================================================
# 脚本名称: 01_import_fasta.sh
# 工具ID:   amp-import-fasta
# 功能说明: 将FASTA格式的扩增子测序数据导入QIIME2 Artifact格式
#           支持 .fasta / .fna / .fa 格式，支持单端和双端数据
# ==============================================================================

# === 默认参数 ===
INPUT_DIR="${1:-./data/raw}"
OUTPUT_DIR="${2:-./results/qiime2}"
INPUT_FORMAT="${3:-SampleData[SequencesWithQuality]}"
MANIFEST_FILE="${4:-manifest.csv}"
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
if [[ ! -d "$INPUT_DIR" ]]; then
    log_error "输入目录不存在: $INPUT_DIR"
    log_error "请确保原始FASTA/FASTQ文件位于指定目录中"
    exit 1
fi

FASTA_COUNT=$(find "$INPUT_DIR" -type f \( -name "*.fasta" -o -name "*.fna" -o -name "*.fa" -o -name "*.fastq" -o -name "*.fq" \) 2>/dev/null | wc -l)
if [[ "$FASTA_COUNT" -eq 0 ]]; then
    log_error "输入目录中未找到任何序列文件 (.fasta/.fna/.fa/.fastq/.fq): $INPUT_DIR"
    exit 1
fi

log_info "找到 ${FASTA_COUNT} 个序列文件"

# === 创建输出目录 ===
mkdir -p "$OUTPUT_DIR"
log_info "输出目录: $OUTPUT_DIR"

# === 检查manifest文件 ===
MANIFEST_PATH="${INPUT_DIR}/${MANIFEST_FILE}"
if [[ ! -f "$MANIFEST_PATH" ]]; then
    log_warn "未找到manifest文件: $MANIFEST_PATH"
    log_warn "正在自动生成manifest文件..."

    # 自动生成manifest文件
    echo "sample-id,absolute-filepath,direction" > "$MANIFEST_PATH"
    for fwd_file in "$INPUT_DIR"/*_R1_*.fastq.gz "$INPUT_DIR"/*_R1_*.fq.gz; do
        [[ -f "$fwd_file" ]] || continue
        sample_name=$(basename "$fwd_file" | sed -E 's/_R1_.*//')
        rev_file=$(echo "$fwd_file" | sed 's/_R1_/_R2_/')

        if [[ -f "$rev_file" ]]; then
            echo "${sample_name},$(realpath "$fwd_file"),forward" >> "$MANIFEST_PATH"
            echo "${sample_name},$(realpath "$rev_file"),reverse" >> "$MANIFEST_PATH"
            log_info "  双端样本: ${sample_name}"
        else
            echo "${sample_name},$(realpath "$fwd_file"),forward" >> "$MANIFEST_PATH"
            log_info "  单端样本: ${sample_name}"
        fi
    done

    log_info "manifest文件已生成: $MANIFEST_PATH"
fi

# === 执行QIIME2导入 ===
log_info "开始导入序列数据到QIIME2格式..."
log_info "  输入类型: $INPUT_FORMAT"
log_info "  线程数: $THREADS"

qiime tools import \
    --type "$INPUT_FORMAT" \
    --input-path "$MANIFEST_PATH" \
    --output-path "${OUTPUT_DIR}/demux.qza" \
    --input-format SingleEndFastqManifestPhred33V2

if [[ $? -eq 0 ]]; then
    log_info "数据导入成功！输出文件: ${OUTPUT_DIR}/demux.qza"

    # 生成可视化摘要
    qiime demux summarize \
        --i-data "${OUTPUT_DIR}/demux.qza" \
        --o-visualization "${OUTPUT_DIR}/demux-summary.qzv" \
        --p-n "$THREADS"

    log_info "可视化摘要已生成: ${OUTPUT_DIR}/demux-summary.qzv"
    log_info "请使用 qiime tools view 查看可视化结果"
else
    log_error "数据导入失败，请检查manifest文件格式和序列文件路径"
    exit 1
fi
