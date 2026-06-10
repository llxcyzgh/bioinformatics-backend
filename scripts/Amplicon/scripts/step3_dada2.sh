#!/bin/bash
# step3_dada2.sh - DADA2 ASV 推断与降噪脚本
# 用法：bash step3_dada2.sh -m <manifest.tsv> [-t trunc_len] [-n threads] [-a min_asv]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
CONDA_BIN="${CONDA_BIN:-/software/anaconda3/bin/conda}"
QIIME_BIN="${QIIME_BIN:-/software/anaconda3/envs/16s-env/bin/qiime}"
BIOM_BIN="${BIOM_BIN:-/software/anaconda3/envs/16s-env/bin/biom}"
FILTER_NAME_PY="${FILTER_NAME_PY:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/filter_name.py}"
ASV_SORT_PL="${ASV_SORT_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/asv_sort.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in CONDA_BIN QIIME_BIN BIOM_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

MANIFEST=""
TRUNC_LEN="0"
THREADS="12"
MIN_ASV="1"

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--manifest) MANIFEST="$2"; shift 2 ;;
        -t|--trunc-len) TRUNC_LEN="$2"; shift 2 ;;
        -n|--threads) THREADS="$2"; shift 2 ;;
        -a|--min-asv) MIN_ASV="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_dada2.sh -m <manifest.tsv> [-t trunc_len] [-n threads] [-a min_asv]"
            echo ""
            echo "参数:"
            echo "  -m, --manifest     manifest 文件路径"
            echo "  -t, --trunc-len    截断长度 (默认：0)"
            echo "  -n, --threads      线程数 (默认：12)"
            echo "  -a, --min-asv      最小 ASV 丰度 (默认：1)"
            echo "  -h, --help         显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${MANIFEST}" ] && { echo "❌ 错误：必须提供 -m"; exit 1; }
[ ! -f "${MANIFEST}" ] && { echo "❌ 错误：manifest 文件不存在：${MANIFEST}"; exit 1; }

# 获取项目目录（manifest 文件所在目录）
PROJECT_DIR="$(cd "$(dirname "${MANIFEST}")" && pwd)"

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
source "${CONDA_BIN}/activate" 16s-env
"${QIIME_BIN}" tools import \
   --type 'SampleData[SequencesWithQuality]' \
   --input-format SingleEndFastqManifestPhred33V2 \
   --input-path "${MANIFEST}" \
   --output-path allFastq.qza

# Step 2: DADA2 去噪
echo "[2/6] DADA2 去噪..."
mkdir -p ConstructASV
cd ConstructASV
"${QIIME_BIN}" dada2 denoise-single \
   --i-demultiplexed-seqs ../allFastq.qza \
   --p-trunc-len ${TRUNC_LEN} \
   --o-table dada2-table.qza \
   --o-representative-sequences dada2-repseq.qza \
   --o-denoising-stats dada2-stats.qza \
   --p-n-threads ${THREADS}

# Step 3: 导出结果
echo "[3/6] 导出结果..."
"${QIIME_BIN}" tools export \
   --input-path dada2-repseq.qza \
   --output-path dada2-repseq_qza
"${QIIME_BIN}" tools export \
   --input-path dada2-stats.qza \
   --output-path dada2-stats_qza
"${QIIME_BIN}" tools export \
   --input-path dada2-table.qza \
   --output-path dada2-table_qza

# Step 4: 格式转换
echo "[4/6] 格式转换..."
"${BIOM_BIN}" convert \
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
"${BIOM_BIN}" convert \
   -i feature-table.tsv \
   -o featureTable.biom \
   --table-type="OTU table" \
   --to-json

sed -i '1s/#OTU ID/ASV-id/' feature-table.tsv

"${QIIME_BIN}" tools import \
   --input-path featureTable.biom \
   --type 'FeatureTable[Frequency]' \
   --input-format BIOMV100Format \
   --output-path featureTable.qza

"${QIIME_BIN}" tools import \
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
