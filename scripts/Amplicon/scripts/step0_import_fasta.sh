#!/bin/bash
# step0_import_fasta.sh - FASTA 导入 QIIME2 脚本
# 用法：bash step0_import_fasta.sh -i <fasta> -o <output_dir>

set -e

FASTA_FILE=""
OUTPUT_DIR=""
SEQ_TYPE="FeatureData[Sequence]"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            FASTA_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -t|--type)
            SEQ_TYPE="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法：bash step0_import_fasta.sh -i <fasta> -o <output>"
            echo ""
            echo "参数:"
            echo "  -i, --input      输入 FASTA 文件"
            echo "  -o, --output     输出目录"
            echo "  -t, --type       QIIME2 类型 (默认：FeatureData[Sequence])"
            echo "                   可选：FeatureData[Sequence], SampleData[SequencesWithQuality]"
            echo "  -h, --help       显示帮助信息"
            exit 0
            ;;
        *)
            echo "错误：未知参数 $1"
            exit 1
            ;;
    esac
done

# ==========================================
# 参数验证
# ==========================================

if [ -z "${FASTA_FILE}" ]; then
    echo "❌ 错误：必须提供输入文件 (-i)"
    exit 1
fi

if [ -z "${OUTPUT_DIR}" ]; then
    echo "❌ 错误：必须提供输出目录 (-o)"
    exit 1
fi

if [ ! -f "${FASTA_FILE}" ]; then
    echo "❌ 错误：FASTA 文件不存在：${FASTA_FILE}"
    exit 1
fi

# ==========================================
# 创建输出目录
# ==========================================

mkdir -p "${OUTPUT_DIR}"

# ==========================================
# 激活 QIIME2 环境
# ==========================================

echo "📥 激活 QIIME2 环境..."
if [ -f /software/anaconda3/bin/activate ]; then
    source /software/anaconda3/bin/activate 16s-env
elif command -v conda &> /dev/null; then
    conda activate 16s-env
else
    echo "⚠️  未找到 QIIME2 环境，请确保已安装并激活 16s-env"
fi

# ==========================================
# 导入 FASTA 为 QIIME2 格式
# ==========================================

echo ""
echo "=========================================="
echo "FASTA 导入 QIIME2"
echo "=========================================="
echo ""

echo "📥 导入 FASTA 文件..."
echo "   输入：${FASTA_FILE}"
echo "   输出：${OUTPUT_DIR}/featureSeqs.qza"
echo "   类型：${SEQ_TYPE}"

BASENAME=$(basename "${FASTA_FILE}" | sed 's/\.[^.]*$//')

qiime tools import \
    --input-path "${FASTA_FILE}" \
    --output-path "${OUTPUT_DIR}/${BASENAME}.qza" \
    --type "${SEQ_TYPE}"

# ==========================================
# 完成
# ==========================================

echo ""
echo "=========================================="
echo "✅ QIIME2 格式导入完成！"
echo "=========================================="
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 输出文件：${OUTPUT_DIR}/${BASENAME}.qza"
echo ""
echo "🔗 下一步："
echo "   物种注释：bash step3_taxonomy.sh -i ${BASENAME}.qza -o Taxonomy_Output/ -t 16S"
echo ""
