#!/bin/bash
# step3_convert_table.sh - 表格转 QIIME2 格式脚本
# 用法：bash step3_convert_table.sh -i <table> -o <output_dir> -t <type>

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

TABLE_FILE=""
OUTPUT_DIR=""
QIIME_TYPE="FeatureTable[Frequency]"
TABLE_TYPE="OTU table"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            TABLE_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -t|--type)
            QIIME_TYPE="$2"
            shift 2
            ;;
        --table-type)
            TABLE_TYPE="$2"
            shift 2
            ;;
        -h|--help)
            echo "用法：bash step3_convert_table.sh -i <table> -o <output> -t <type>"
            echo ""
            echo "参数:"
            echo "  -i, --input        输入表格文件 (TSV/BIOM)"
            echo "  -o, --output       输出目录"
            echo "  -t, --type         QIIME2 类型 (默认：FeatureTable[Frequency])"
            echo "                     可选：FeatureTable[Frequency], FeatureData[Sequence]"
            echo "  --table-type       表格类型 (默认：OTU table)"
            echo "                     可选：OTU table, Observation metadata"
            echo "  -h, --help         显示帮助信息"
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

if [ -z "${TABLE_FILE}" ]; then
    echo "❌ 错误：必须提供输入文件 (-i)"
    exit 1
fi

if [ -z "${OUTPUT_DIR}" ]; then
    echo "❌ 错误：必须提供输出目录 (-o)"
    exit 1
fi

if [ ! -f "${TABLE_FILE}" ]; then
    echo "❌ 错误：文件不存在：${TABLE_FILE}"
    exit 1
fi

# ==========================================
# 创建输出目录
# ==========================================

# ----- 路径转绝对路径（cd 输出目录前） -----
TABLE_FILE="$(abs_path_file "${TABLE_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"

# ==========================================
# 获取文件名
# ==========================================

BASENAME=$(basename "${TABLE_FILE}" | sed 's/\.[^.]*$//')

# ==========================================
# 激活 QIIME2 环境
# ==========================================

echo "📥 激活 QIIME2 环境..."
source "${CONDA_BIN}/activate" "${CONDA_ENV}"

# ==========================================
# 转换流程
# ==========================================

echo ""
echo "=========================================="
echo "表格转 QIIME2 格式"
echo "=========================================="
echo ""

# Step 1: TSV → BIOM (如果是 TSV 文件)
if [[ "${TABLE_FILE}" == *.txt ]] || [[ "${TABLE_FILE}" == *.tsv ]]; then
    echo "[1/2] 检测到 TSV 文件，转换为 BIOM..."
    echo "   输入：${TABLE_FILE}"
    
    biom convert \
        -i "${TABLE_FILE}" \
        -o "${OUTPUT_DIR}/${BASENAME}.biom" \
        --to-json \
        --table-type="${TABLE_TYPE}"
    
    TABLE_FILE="${OUTPUT_DIR}/${BASENAME}.biom"
    echo "   输出：${TABLE_FILE}"
    echo "   ✅ BIOM 转换完成"
fi

# Step 2: BIOM → QZA
echo "[2/2] 导入为 QIIME2 格式..."
echo "   输入：${TABLE_FILE}"
echo "   类型：${QIIME_TYPE}"

qiime tools import \
    --input-path "${TABLE_FILE}" \
    --input-format BIOMV100Format \
    --type "${QIIME_TYPE}" \
    --output-path "${OUTPUT_DIR}/${BASENAME}.qza"

echo "   输出：${OUTPUT_DIR}/${BASENAME}.qza"
echo "   ✅ QIIME2 格式导入完成"

# ==========================================
# 完成
# ==========================================

echo ""
echo "=========================================="
echo "✅ 表格转换完成！"
echo "=========================================="
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 输出文件：${OUTPUT_DIR}/${BASENAME}.qza"
echo ""
