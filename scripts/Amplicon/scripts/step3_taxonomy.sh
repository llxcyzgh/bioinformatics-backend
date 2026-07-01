#!/bin/bash
# step3_taxonomy.sh - 物种注释脚本
# 用法：bash step3_taxonomy.sh -i <featureSeqs.qza|sequences.fasta> -t <16S|18S|ITS> [-p threads] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
CONDA_BIN="${CONDA_BIN:-/software/anaconda3/bin}"
CONDA_ENV="${CONDA_ENV:-16s-env}"

# 参考数据库路径（支持环境变量覆盖）
# 16S 数据库
SILVA_16S_SEQ="${SILVA_16S_SEQ:-/database/amplicon/Qiime2_SILVA_v138.1/16S.Bac.Arc/silva_138.1_99_16S.qza}"
SILVA_16S_TAX="${SILVA_16S_TAX:-/database/amplicon/Qiime2_SILVA_v138.1/16S.Bac.Arc/silva_138.1_99_16S_taxonomy.qza}"

# 18S 数据库
SILVA_18S_SEQ="${SILVA_18S_SEQ:-/database/amplicon/Qiime2_SILVA_v138.1/18S.Eukaryota/silva_Eukaryota.qza}"
SILVA_18S_TAX="${SILVA_18S_TAX:-/database/amplicon/Qiime2_SILVA_v138.1/18S.Eukaryota/silva_Eukaryota.taxonmy.qza}"

# ITS 数据库（UNITE）
UNITE_SEQ="${UNITE_SEQ:-/database/amplicon/Qiime2_unite99_v9.0/unitev9.0_seq_99.qza}"
UNITE_TAX="${UNITE_TAX:-/database/amplicon/Qiime2_unite99_v9.0/unitev9.0_tax_99.qza}"

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
AMP_TYPE="16S"
THREADS="16"
TEMP_FILE=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_FILE="$2"; shift 2 ;;
        -t|--type) AMP_TYPE="$2"; shift 2 ;;
        -p|--threads) THREADS="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_taxonomy.sh -i <featureSeqs.qza|sequences.fasta> -t <16S|18S|ITS> [-p threads]"
            echo ""
            echo "参数:"
            echo "  -i, --input      输入文件路径（支持 .qza 或 .fasta/.fa/.fna）"
            echo "  -t, --type       扩增子类型 (16S、18S 或 ITS，默认：16S)"
            echo "  -p, --threads    线程数 (默认：16)"
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

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
# ----- 路径转绝对路径（cd 输出目录前） -----
INPUT_FILE="$(abs_path_file "${INPUT_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

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
       --output-path "${OUTPUT_DIR}/featureSeqs_temp.qza"
    
    # 验证转换结果
    if [ ! -f "featureSeqs_temp.qza" ]; then
        echo "❌ 错误：FASTA 转 qza 失败"
        exit 1
    fi
    
    echo "✅ 转换完成：${INPUT_FILE} → featureSeqs_temp.qza"
    REP_SEQ="${OUTPUT_DIR}/featureSeqs_temp.qza"
    TEMP_FILE="${OUTPUT_DIR}/featureSeqs_temp.qza"  # 标记为临时文件
else
    echo "❌ 错误：不支持的文件格式：${INPUT_FILE}"
    echo "   支持的格式：.qza, .fasta, .fa, .fna"
    exit 1
fi

# 根据扩增子类型选择参考数据库
if [ "${AMP_TYPE}" = "16S" ]; then
    REF_SEQ="${SILVA_16S_SEQ}"
    REF_TAX="${SILVA_16S_TAX}"
elif [ "${AMP_TYPE}" = "18S" ]; then
    REF_SEQ="${SILVA_18S_SEQ}"
    REF_TAX="${SILVA_18S_TAX}"
else
    REF_SEQ="${UNITE_SEQ}"
    REF_TAX="${UNITE_TAX}"
fi

# 验证参考数据库
if [ ! -f "${REF_SEQ}" ]; then
    echo "❌ 错误：参考序列数据库不存在：${REF_SEQ}"
    exit 1
fi
if [ ! -f "${REF_TAX}" ]; then
    echo "❌ 错误：参考注释数据库不存在：${REF_TAX}"
    exit 1
fi

echo ""
echo "=========================================="
echo "物种注释"
echo "=========================================="
echo ""

echo "🔬 执行物种注释..."
echo "   输入文件：${INPUT_FILE}"
echo "   输入格式：${INPUT_FORMAT}"
echo "   扩增子类型：${AMP_TYPE}"
echo "   参考序列：${REF_SEQ}"
echo "   参考注释：${REF_TAX}"
echo "   线程数：${THREADS}"
echo "   输出目录：${OUTPUT_DIR}"
echo ""

# 激活 conda 环境（如果之前没激活）
if [ "${INPUT_FORMAT}" != "fasta" ]; then
    source "${CONDA_BIN}/activate" "${CONDA_ENV}"
fi

# Step 1: VSEARCH 比对
echo "[1/3] VSEARCH 比对..."
qiime feature-classifier classify-consensus-vsearch \
   --i-query "${REP_SEQ}" \
   --p-threads ${THREADS} \
   --i-reference-reads "${REF_SEQ}" \
   --i-reference-taxonomy "${REF_TAX}" \
   --o-classification seq_taxonomy.qza \
   --o-search-results taxonomy.qza

# Step 2: 导出结果
echo "[2/3] 导出结果..."
qiime tools export \
   --input-path seq_taxonomy.qza \
   --output-path seq_taxonomy_qza

# Step 3: 格式化处理
echo "[3/3] 格式化处理..."
chmod 755 seq_taxonomy_qza/taxonomy.tsv

# 替换分类学前缀（d__ → k__）
sed -i 's/d__/k__/g' seq_taxonomy_qza/taxonomy.tsv

# 替换表头
sed -i '1s/Feature ID/#OTU ID/g' seq_taxonomy_qza/taxonomy.tsv
sed -i '1s/Taxon/taxonomy/g' seq_taxonomy_qza/taxonomy.tsv
sed -i '1s/Confidence/confidence/g' seq_taxonomy_qza/taxonomy.tsv

# 去掉 # 和 :
sed -i '2,$s/#//g;2,$s/://g' seq_taxonomy_qza/taxonomy.tsv

# 创建符号链接
ln -sf seq_taxonomy_qza/taxonomy.tsv all_tax_assignments.txt


# 清理临时文件
if [ -n "${TEMP_FILE}" ]; then
    rm -f "${TEMP_FILE}"
    echo "🗑️  已清理临时文件：${TEMP_FILE}"
fi

echo ""
echo "✅ 物种注释完成"
echo ""
echo "📊 输出文件:"
echo "   - seq_taxonomy.qza: 物种注释结果（QIIME2）"
echo "   - taxonomy.tsv: 物种注释表（文本）"
echo "   - all_tax_assignments.txt: 物种注释表（符号链接）"
echo ""
