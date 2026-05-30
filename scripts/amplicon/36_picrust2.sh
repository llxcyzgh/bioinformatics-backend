#!/bin/bash
# ============================================================
# PICRUSt2功能预测 (tool_id: amp-funpre)
# 描述：使用PICRUSt2对16S rRNA基因序列进行功能基因预测
#   预测KEGG通路、MetaCyc通路和EC编号丰度
# 输入：FASTA序列文件 (seqs.fasta), OTU表 (otu.tsv)
# 输出：KEGG通路丰度、MetaCyc通路丰度、EC编号丰度
# ============================================================

set -euo pipefail

# ---- 参数解析 ----
INPUT_DIR="${1:-.}"
OUTPUT_DIR="${2:-.}"
THREADS="${3:-4}"

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

echo "========================================"
echo "PICRUSt2 功能预测分析"
echo "========================================"

# ---- 检查输入文件 ----
SEQ_FILE="$INPUT_DIR/seqs.fasta"
OTU_FILE="$INPUT_DIR/otu.tsv"

if [ ! -f "$SEQ_FILE" ]; then
    echo "错误：找不到序列文件 seqs.fasta"
    exit 1
fi

if [ ! -f "$OTU_FILE" ]; then
    echo "错误：找不到OTU表 otu.tsv"
    exit 1
fi

echo "序列文件: $SEQ_FILE"
echo "OTU表: $OTU_FILE"
echo "输出目录: $OUTPUT_DIR"
echo "线程数: $THREADS"

# ---- 检查PICRUSt2是否安装 ----
if ! command -v picrust2_pipeline.py &> /dev/null; then
    echo "错误：PICRUSt2未安装"
    echo "请使用以下命令安装："
    echo "  conda create -n picrust2 -c bioconda picrust2"
    echo "  conda activate picrust2"
    exit 1
fi

echo "PICRUSt2版本信息："
picrust2_pipeline.py --version 2>/dev/null || echo "版本信息不可用"

# ---- 步骤1：序列放置到参考树 ----
echo ""
echo "[步骤1/4] 将ASV/OTU序列放置到PICRUSt2参考树..."
place_seqs.py -s "$SEQ_FILE" -o "$OUTPUT_DIR/placed_seqs.tre" \
    -p "$THREADS" --intermediate "$OUTPUT_DIR/intermediate"

# ---- 步骤2：预测16S拷贝数 ----
echo ""
echo "[步骤2/4] 预测16S rRNA基因拷贝数..."
hsp.py -i "$OUTPUT_DIR/placed_seqs.tre" \
    -t 16S \
    -o "$OUTPUT_DIR/16S_predicted.tsv" \
    -p "$THREADS" \
    --intermediate "$OUTPUT_DIR/intermediate"

# ---- 步骤3：预测功能基因 ----
echo ""
echo "[步骤3/4] 预测EC编号丰度..."
hsp.py -i "$OUTPUT_DIR/placed_seqs.tre" \
    -t EC \
    -o "$OUTPUT_DIR/EC_predicted.tsv" \
    -p "$THREADS" \
    --intermediate "$OUTPUT_DIR/intermediate"

echo "预测KO通路..."
hsp.py -i "$OUTPUT_DIR/placed_seqs.tre" \
    -t KO \
    -o "$OUTPUT_DIR/KO_predicted.tsv" \
    -p "$THREADS" \
    --intermediate "$OUTPUT_DIR/intermediate"

echo "预测MetaCyc通路..."
hsp.py -i "$OUTPUT_DIR/placed_seqs.tre" \
    -t METACYC \
    -o "$OUTPUT_DIR/METACYC_predicted.tsv" \
    -p "$THREADS" \
    --intermediate "$OUTPUT_DIR/intermediate"

# ---- 步骤4：计算丰度 ----
echo ""
echo "[步骤4/4] 计算功能基因丰度..."

# 将OTU表转换为PICRUSt2格式（BIOM）
# 检查是否有biom工具
if command -v biom convert &> /dev/null; then
    # 转换为BIOM格式
    biom convert -i "$OTU_FILE" -o "$OUTPUT_DIR/otu_table.biom" \
        --to-hdf5 --table-type "OTU table" 2>/dev/null || \
    cp "$OTU_FILE" "$OUTPUT_DIR/otu_table.tsv"
    OTU_INPUT="$OUTPUT_DIR/otu_table.biom"
else
    # 直接使用TSV格式
    cp "$OTU_FILE" "$OUTPUT_DIR/otu_table.tsv"
    OTU_INPUT="$OUTPUT_DIR/otu_table.tsv"
fi

# 乘以预测拷贝数得到丰度
echo "计算EC丰度..."
mul_by_NSTI.py -i "$OUTPUT_DIR/EC_predicted.tsv" \
    -n "$OUTPUT_DIR/16S_predicted.tsv" \
    -o "$OUTPUT_DIR/EC_abundance.tsv" 2>/dev/null || \
cp "$OUTPUT_DIR/EC_predicted.tsv" "$OUTPUT_DIR/EC_abundance.tsv"

echo "计算KO丰度..."
mul_by_NSTI.py -i "$OUTPUT_DIR/KO_predicted.tsv" \
    -n "$OUTPUT_DIR/16S_predicted.tsv" \
    -o "$OUTPUT_DIR/KO_abundance.tsv" 2>/dev/null || \
cp "$OUTPUT_DIR/KO_predicted.tsv" "$OUTPUT_DIR/KO_abundance.tsv"

echo "计算MetaCyc丰度..."
mul_by_NSTI.py -i "$OUTPUT_DIR/METACYC_predicted.tsv" \
    -n "$OUTPUT_DIR/16S_predicted.tsv" \
    -o "$OUTPUT_DIR/METACYC_abundance.tsv" 2>/dev/null || \
cp "$OUTPUT_DIR/METACYC_predicted.tsv" "$OUTPUT_DIR/METACYC_abundance.tsv"

# ---- 输出结果摘要 ----
echo ""
echo "========================================"
echo "PICRUSt2功能预测完成！"
echo "========================================"
echo "输出文件："
echo "  EC丰度:      $OUTPUT_DIR/EC_abundance.tsv"
echo "  KO丰度:      $OUTPUT_DIR/KO_abundance.tsv"
echo "  MetaCyc丰度: $OUTPUT_DIR/METACYC_abundance.tsv"
echo "  16S拷贝数:   $OUTPUT_DIR/16S_predicted.tsv"
echo ""
echo "NSTI分数（衡量预测可靠性）："
if [ -f "$OUTPUT_DIR/intermediate/marker_nsti.txt" ]; then
    head -5 "$OUTPUT_DIR/intermediate/marker_nsti.txt"
fi
echo ""
echo "提示：NSTI < 2 表示预测较为可靠"
echo "========================================"
