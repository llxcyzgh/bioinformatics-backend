#!/bin/bash
# step3_dada2.sh - DADA2 ASV 推断与降噪脚本
# 用法：bash step3_dada2.sh -m <manifest.tsv> [-t trunc_len] [-n threads] [-a min_asv] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
CONDA_BIN="${CONDA_BIN:-/software/anaconda3/bin}"
CONDA_ENV="${CONDA_ENV:-16s-env}"
FILTER_NAME_PY="${FILTER_NAME_PY:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/filter_name.py}"
ASV_SORT_PL="${ASV_SORT_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/asv_sort.pl}"

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

MANIFEST=""
TRUNC_LEN="0"
THREADS="12"
MIN_ASV="1"
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--manifest) MANIFEST="$2"; shift 2 ;;
        -t|--trunc-len) TRUNC_LEN="$2"; shift 2 ;;
        -n|--threads) THREADS="$2"; shift 2 ;;
        -a|--min-asv) MIN_ASV="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_dada2.sh -m <manifest.tsv> [-t trunc_len] [-n threads] [-a min_asv]"
            echo ""
            echo "参数:"
            echo "  -m, --manifest     manifest 文件路径"
            echo "  -t, --trunc-len    截断长度 (默认：0)"
            echo "  -n, --threads      线程数 (默认：12)"
            echo "  -a, --min-asv      最小 ASV 丰度 (默认：1)"
            echo "  -o, --output     输出目录"

            echo "  -h, --help         显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${MANIFEST}" ] && { echo "❌ 错误：必须提供 -m"; exit 1; }
[ ! -f "${MANIFEST}" ] && { echo "❌ 错误：manifest 文件不存在：${MANIFEST}"; exit 1; }

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# ----- 路径转绝对路径（cd 输出目录前） -----
MANIFEST="$(abs_path_file "${MANIFEST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
PROJECT_DIR="$(cd "${OUTPUT_DIR}" && pwd)"

echo ""
echo "=========================================="
echo "DADA2 ASV 推断与降噪"
echo "=========================================="
echo ""

echo "📊 执行 DADA2 分析..."
echo "   manifest: ${MANIFEST}"
echo "   项目目录：${PROJECT_DIR}"
echo "   截断长度：${TRUNC_LEN}"
echo "   线程数：${THREADS}"
echo ""

cd "${PROJECT_DIR}"

# Step 1: 导入序列到 QIIME2
echo "[1/6] 导入序列到 QIIME2..."
source "${CONDA_BIN}/activate" "${CONDA_ENV}"
qiime tools import \
   --type 'SampleData[SequencesWithQuality]' \
   --input-format SingleEndFastqManifestPhred33V2 \
   --input-path "${MANIFEST}" \
   --output-path allFastq.qza

# Step 2: DADA2 去噪
echo "[2/6] DADA2 去噪..."
qiime dada2 denoise-single \
   --i-demultiplexed-seqs allFastq.qza \
   --p-trunc-len ${TRUNC_LEN} \
   --o-table dada2-table.qza \
   --o-representative-sequences dada2-repseq.qza \
   --o-denoising-stats dada2-stats.qza \
   --p-n-threads ${THREADS}

# Step 3: 导出结果
echo "[3/6] 导出结果..."
qiime tools export \
   --input-path dada2-repseq.qza \
   --output-path dada2-repseq_qza
qiime tools export \
   --input-path dada2-stats.qza \
   --output-path dada2-stats_qza
qiime tools export \
   --input-path dada2-table.qza \
   --output-path dada2-table_qza

# Step 4: 格式转换
echo "[4/6] 格式转换..."
biom convert \
   -i dada2-table_qza/feature-table.biom \
   -o dada2-table_qza/feature-table.tsv \
   --to-tsv

# Step 5: ASV 过滤与排序
echo "[5/6] ASV 过滤与排序..."
python "${FILTER_NAME_PY}" \
   dada2-table_qza/feature-table.tsv \
   dada2-repseq_qza/dna-sequences.fasta \
   ${MIN_ASV}

sed '1s/ASV-id/#OTU ID/' featureTable.txt > featureTable.nosort.txt

# 如果有 group 文件则使用，否则跳过排序
if [ -f "../group.list" ]; then
    perl "${ASV_SORT_PL}" \
       --table featureTable.nosort.txt \
       --group ../group.list \
       --new_table feature-table.tsv
    rm -f featureTable.nosort.txt
else
    mv featureTable.nosort.txt feature-table.tsv
fi

# Step 6: 导入回 QIIME2
echo "[6/6] 导入回 QIIME2..."
biom convert \
   -i feature-table.tsv \
   -o featureTable.biom \
   --table-type="OTU table" \
   --to-json

sed -i '1s/#OTU ID/ASV-id/' feature-table.tsv

qiime tools import \
   --input-path featureTable.biom \
   --type 'FeatureTable[Frequency]' \
   --input-format BIOMV100Format \
   --output-path featureTable.qza

qiime tools import \
   --input-path feature.fasta \
   --output-path featureSeqs.qza \
   --type 'FeatureData[Sequence]'

# 清理临时文件
rm -rf dada2-repseq_qza dada2-stats_qza dada2-table_qza
rm -f dada2-repseq.qza dada2-stats.qza dada2-table.qza
rm -f featureTable.txt dada2-stats.qzv

echo ""
echo "✅ DADA2 ASV 推断与降噪完成"
echo ""
echo "📊 输出文件:"
echo "   - featureSeqs.qza: ASV 代表序列（QIIME2）"
echo "   - feature-table.tsv: ASV 丰度表（排序后）"
echo "   - feature.fasta: ASV 代表序列（FASTA）"
echo "   - featureTable.qza: ASV 丰度表（QIIME2）"
echo "   - featureTable.biom: ASV 丰度表（BIOM）"
echo ""
