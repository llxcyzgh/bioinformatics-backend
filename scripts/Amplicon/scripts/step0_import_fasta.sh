#!/bin/bash
# step0_import_fasta.sh - FASTA 导入 QIIME2 脚本
# 用法：bash step0_import_fasta.sh -i <fasta> -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
CONDA_BIN="${CONDA_BIN:-/software/anaconda3/bin}"
CONDA_ENV="${CONDA_ENV:-16s-env}"

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -f "${CONDA_BIN}/activate" ]; then
    echo "❌ 错误：CONDA activate 不存在：${CONDA_BIN}/activate"
    echo "   可通过环境变量覆盖，例如：export CONDA_BIN=\"/your/path/to/anaconda3/bin\" CONDA_ENV=\"16s-env\""
    exit 1
fi

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

# ----- 路径转绝对路径（cd 输出目录前） -----
FASTA_FILE="$(abs_path_file "${FASTA_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"

# ==========================================
# 激活 QIIME2 环境
# ==========================================

echo "📥 激活 QIIME2 环境..."
source "${CONDA_BIN}/activate" "${CONDA_ENV}"

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
