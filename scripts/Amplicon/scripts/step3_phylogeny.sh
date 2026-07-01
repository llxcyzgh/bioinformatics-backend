#!/bin/bash
# step3_phylogeny.sh - 系统发育树构建脚本
# 用法：bash step3_phylogeny.sh -i <featureSeqs.qza|sequences.fasta> [-n threads] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
CONDA_BIN="${CONDA_BIN:-/software/anaconda3/bin}"
CONDA_ENV="${CONDA_ENV:-16s-env}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -f "${CONDA_BIN}/activate" ]; then
    echo "❌ 错误：CONDA activate 不存在：${CONDA_BIN}/activate"
    echo "   可通过环境变量覆盖，例如：export CONDA_BIN=\"/your/path/to/anaconda3/bin\" CONDA_ENV=\"16s-env\""
    exit 1
fi

INPUT_FILE=""
THREADS="12"
TEMP_FILE=""

OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_FILE="$2"; shift 2 ;;
        -n|--threads) THREADS="$2"; shift 2 ;;
                -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step3_phylogeny.sh -i <featureSeqs.qza|sequences.fasta> [-n threads]"
            echo ""
            echo "参数:"
            echo "  -i, --input      输入文件路径（支持 .qza 或 .fasta/.fa/.fna）"
            echo "  -n, --threads    线程数 (默认：12)"
            echo "  -o, --output     输出目录"

            echo "  -h, --help       显示帮助"
            echo ""
            echo "输入格式支持："
            echo "  - QIIME2 qza 格式：featureSeqs.qza（step3_dada2 输出）"
            echo "  - FASTA 格式：sequences.fasta/.fa/.fna（用户提供）"
            echo ""
            echo "自动格式检测："
            echo "  脚本自动检测输入文件格式，如果是 FASTA 格式，自动转换为 QIIME2 qza 格式"
            echo "  转换过程透明，完成后自动清理临时文件"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INPUT_FILE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ ! -f "${INPUT_FILE}" ] && { echo "❌ 错误：输入文件不存在：${INPUT_FILE}"; exit 1; }

# ===== 自动检测输入格式并转换 =====
INPUT_FORMAT=""
if [[ "${INPUT_FILE}" == *.qza ]]; then
    INPUT_FORMAT="qza"
    echo "✅ 检测到 QIIME2 qza 格式"
    REP_SEQ="${INPUT_FILE}"
elif [[ "${INPUT_FILE}" == *.fasta || "${INPUT_FILE}" == *.fa || "${INPUT_FILE}" == *.fna ]]; then
    INPUT_FORMAT="fasta"
    echo "✅ 检测到 FASTA 格式，将转换为 QIIME2 qza..."
    
    # 激活 conda 环境
    source "${CONDA_BIN}/activate" "${CONDA_ENV}"
    
    # 转换为 qza
    qiime tools import \
       --type 'FeatureData[Sequence]' \
       --input-format DNAFASTAFormat \
       --input-path "${INPUT_FILE}" \
       --output-path featureSeqs_temp.qza
    
    # 验证转换结果
    if [ ! -f "featureSeqs_temp.qza" ]; then
        echo "❌ 错误：FASTA 转 qza 失败"
        exit 1
    fi
    
    echo "✅ 转换完成：${INPUT_FILE} → featureSeqs_temp.qza"
    REP_SEQ="featureSeqs_temp.qza"
    TEMP_FILE="featureSeqs_temp.qza"  # 标记为临时文件
else
    echo "❌ 错误：不支持的文件格式：${INPUT_FILE}"
    echo "   支持的格式：.qza, .fasta, .fa, .fna"
    exit 1
fi

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# ----- 路径转绝对路径（cd 输出目录前） -----
INPUT_FILE="$(abs_path_file "${INPUT_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "系统发育树构建"
echo "=========================================="
echo ""

echo "🌳 执行进化树构建..."
echo "   输入文件：${INPUT_FILE}"
echo "   输入格式：${INPUT_FORMAT}"
echo "   线程数：${THREADS}"
echo ""

# 激活 conda 环境（如果之前没激活）
if [ "${INPUT_FORMAT}" != "fasta" ]; then
    source "${CONDA_BIN}/activate" "${CONDA_ENV}"
fi

# Step 1: 多序列比对 + 构建进化树
echo "[1/2] 多序列比对 (mafft) + 构建进化树 (fasttree)..."
qiime phylogeny align-to-tree-mafft-fasttree \
   --i-sequences "${REP_SEQ}" \
   --o-alignment aligned-rep-seqs.qza \
   --o-masked-alignment masked-aligned-rep-seqs.qza \
   --o-tree unrooted-tree.qza \
   --o-rooted-tree rooted-tree.qza \
   --p-n-threads ${THREADS}

# Step 2: 导出 Newick 格式
echo "[2/2] 导出 Newick 格式..."
qiime tools export \
   --input-path rooted-tree.qza \
   --output-path rooted-tree_qza
qiime tools export \
   --input-path unrooted-tree.qza \
   --output-path unrooted-tree_qza

# 重命名为更友好的文件名
mv rooted-tree_qza/tree.nwk rooted_tree.nwk 2>/dev/null || true
mv unrooted-tree_qza/tree.nwk unrooted_tree.nwk 2>/dev/null || true

# 清理临时文件
if [ -n "${TEMP_FILE}" ]; then
    rm -f "${TEMP_FILE}"
    echo "🗑️  已清理临时文件：${TEMP_FILE}"
fi

# 清理临时目录
rm -rf rooted-tree_qza unrooted-tree_qza

echo ""
echo "✅ 系统发育树构建完成"
echo ""
echo "📊 输出文件:"
echo "   - rooted-tree.qza: 有根系统发育树（QIIME2）"
echo "   - unrooted-tree.qza: 无根系统发育树（QIIME2）"
echo "   - rooted_tree.nwk: 有根系统发育树（Newick）"
echo "   - unrooted_tree.nwk: 无根系统发育树（Newick）"
echo ""
