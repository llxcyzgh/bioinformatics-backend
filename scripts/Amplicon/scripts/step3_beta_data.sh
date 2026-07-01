#!/bin/bash
# step3_beta_data.sh - Beta 多样性分析脚本
# 用法：bash step3_beta_data.sh -i <asv_table.even.txt> -t <tree> -m <meta> -o <output_dir>

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

EVEN_TABLE=""
TREE_FILE=""
META_FILE=""
OUTPUT_DIR=""
SAMPLING_DEPTH="${SAMPLING_DEPTH:-}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) EVEN_TABLE="$2"; shift 2 ;;
        -t|--tree) TREE_FILE="$2"; shift 2 ;;
        -m|--meta) META_FILE="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -d|--depth) SAMPLING_DEPTH="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_beta_data.sh -i <asv_table.even.txt> -t <tree> -m <meta> -o <output> [-d <depth>]"
            echo ""
            echo "参数:"
            echo "  -i, --input      均一化 ASV 表（TSV/TXT，也支持 QZA）"
            echo "  -t, --tree       有根系统发育树（QZA）"
            echo "  -m, --meta       样本元数据文件（需含 #SampleID、Description 表头，缺失时自动补全）"
            echo "  -o, --output     输出目录"
            echo "  -d, --depth      采样深度（默认：自动取所有样本中最小 reads 数）"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${EVEN_TABLE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ ! -f "${EVEN_TABLE}" ] && { echo "❌ 错误：均一化表不存在：${EVEN_TABLE}"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# ----- 路径转绝对路径（cd 输出目录前） -----
EVEN_TABLE="$(abs_path_file "${EVEN_TABLE}")"
TREE_FILE="$(abs_path_file_optional "${TREE_FILE}")"
META_FILE="$(abs_path_file_optional "${META_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "Beta 多样性分析"
echo "=========================================="
echo ""

if [ -z "${TREE_FILE}" ] || [ -z "${META_FILE}" ]; then
    echo "⚠️  缺少树文件或元数据，跳过 Beta 多样性分析"
    exit 0
fi

[ ! -f "${META_FILE}" ] && { echo "❌ 错误：元数据文件不存在：${META_FILE}"; exit 1; }

# 验证元数据表头；QIIME2 要求首行为 #SampleID	Description
_meta_first_line=$(head -1 "${META_FILE}" | tr -d '\r')
META_FILE_QIIME="${META_FILE}"
if [[ "${_meta_first_line}" != "#SampleID	Description" ]]; then
    META_FILE_QIIME="${OUTPUT_DIR}/metadata.qiime.mf"
    if [[ "${_meta_first_line}" == "SampleID	Description" ]]; then
        echo "📝 元数据表头缺少 # 前缀，自动修正..."
        {
            printf '#SampleID\tDescription\n'
            tail -n +2 "${META_FILE}"
        } > "${META_FILE_QIIME}"
    else
        echo "📝 元数据缺少表头 #SampleID	Description，自动补全..."
        {
            printf '#SampleID\tDescription\n'
            cat "${META_FILE}"
        } > "${META_FILE_QIIME}"
    fi
    echo "   ✅ 已生成 ${META_FILE_QIIME}"
fi

echo "📊 输入文件：${EVEN_TABLE}"
echo "📊 系统发育树：${TREE_FILE}"
echo "📊 样本元数据：${META_FILE_QIIME}"
echo ""

source "${CONDA_BIN}/activate" "${CONDA_ENV}"

# TSV/TXT → QZA（借鉴 step3_alpha_data.sh）；若已是 QZA 则直接使用
CONVERTED_FROM_TXT=0
if [[ "${EVEN_TABLE}" == *.qza ]]; then
    EVEN_TABLE_QZA="${EVEN_TABLE}"
    echo "📥 输入为 QZA，跳过格式转换"
else
    CONVERTED_FROM_TXT=1
    echo "[1/3] BIOM 转换..."
    biom convert \
        -i "${EVEN_TABLE}" \
        -o asv_table.even.biom \
        --to-json \
        --table-type="OTU table"

    echo "[2/3] 导入 QIIME2..."
    qiime tools import \
        --input-path asv_table.even.biom \
        --type 'FeatureTable[Frequency]' \
        --input-format BIOMV100Format \
        --output-path asv_table.even.qza

    rm -f asv_table.even.biom
    EVEN_TABLE_QZA="asv_table.even.qza"
    echo "   ✅ 已生成 ${EVEN_TABLE_QZA}"
fi

# 自动计算采样深度：所有样本中 reads 总数的最小值
if [ -z "${SAMPLING_DEPTH}" ]; then
    if [ "${CONVERTED_FROM_TXT}" -eq 1 ]; then
        echo "[3/3] 自动计算采样深度..."
    else
        echo "📊 自动计算采样深度..."
    fi
    _DEPTH_TMP="${OUTPUT_DIR}/.sampling_depth_tmp"
    mkdir -p "${_DEPTH_TMP}"

    qiime feature-table summarize \
        --i-table "${EVEN_TABLE_QZA}" \
        --o-visualization "${_DEPTH_TMP}/table_summary.qzv"

    qiime tools export \
        --input-path "${_DEPTH_TMP}/table_summary.qzv" \
        --output-path "${_DEPTH_TMP}/export"

    SAMPLING_DEPTH=$(tail -n +2 "${_DEPTH_TMP}/export/sample-frequency-detail.csv" \
        | cut -d',' -f2 \
        | awk '{v=int($1); if(v>0) print v}' \
        | sort -n \
        | head -1)

    rm -rf "${_DEPTH_TMP}"

    if [ -z "${SAMPLING_DEPTH}" ] || [ "${SAMPLING_DEPTH}" -lt 1 ]; then
        echo "❌ 错误：无法从特征表计算有效采样深度"
        exit 1
    fi
    echo "   采样深度（最小样本 reads 数）：${SAMPLING_DEPTH}"
else
    echo "📊 使用指定采样深度：${SAMPLING_DEPTH}"
fi

echo ""
echo "🔬 执行 Beta 多样性核心分析..."
qiime diversity core-metrics-phylogenetic \
    --i-phylogeny "${TREE_FILE}" \
    --i-table "${EVEN_TABLE_QZA}" \
    --p-sampling-depth "${SAMPLING_DEPTH}" \
    --m-metadata-file "${META_FILE_QIIME}" \
    --p-n-jobs-or-threads 3 \
    --o-rarefied-table rarefied_table.qza \
    --o-faith-pd-vector faith_pd_vector.qza \
    --o-observed-features-vector observed_otus_vector.qza \
    --o-shannon-vector shannon_vector.qza \
    --o-evenness-vector evenness_vector.qza \
    --o-unweighted-unifrac-distance-matrix unweighted_unifrac_distance_matrix.qza \
    --o-weighted-unifrac-distance-matrix weighted_unifrac_distance_matrix.qza \
    --o-jaccard-distance-matrix jaccard_distance_matrix.qza \
    --o-bray-curtis-distance-matrix bray_curtis_distance_matrix.qza \
    --o-unweighted-unifrac-pcoa-results unweighted_unifrac_pcoa_results.qza \
    --o-weighted-unifrac-pcoa-results weighted_unifrac_pcoa_results.qza \
    --o-jaccard-pcoa-results jaccard_pcoa_results.qza \
    --o-bray-curtis-pcoa-results bray_curtis_pcoa_results.qza \
    --o-unweighted-unifrac-emperor unweighted_unifrac_emperor.qzv \
    --o-weighted-unifrac-emperor weighted_unifrac_emperor.qzv \
   --o-jaccard-emperor jaccard_emperor.qzv \
   --o-bray-curtis-emperor bray_curtis_emperor.qzv

echo ""
echo "📤 导出 QZA/QZV 结果..."
for index in rarefied_table faith_pd_vector observed_otus_vector shannon_vector evenness_vector \
    unweighted_unifrac_distance_matrix weighted_unifrac_distance_matrix \
    jaccard_distance_matrix bray_curtis_distance_matrix \
    unweighted_unifrac_pcoa_results weighted_unifrac_pcoa_results \
    jaccard_pcoa_results bray_curtis_pcoa_results; do
    echo "  导出 ${index}.qza → ${index}_qza/"
    qiime tools export \
        --input-path "${index}.qza" \
        --output-path "${index}_qza"
done

for index in unweighted_unifrac_emperor weighted_unifrac_emperor jaccard_emperor bray_curtis_emperor; do
    echo "  导出 ${index}.qzv → ${index}_qzv/"
    qiime tools export \
        --input-path "${index}.qzv" \
        --output-path "${index}_qzv"
done

echo ""
echo "✅ Beta 多样性分析完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
if [ "${CONVERTED_FROM_TXT}" -eq 1 ]; then
    echo "   - asv_table.even.qza: QIIME2 特征表"
fi
echo "   - *_emperor.qzv: Emperor 交互式可视化"
echo "   - *_distance_matrix.qza: 距离矩阵"
echo "   - *_qza/: QZA 解压结果（距离矩阵、PCoA 坐标等）"
echo "   - *_qzv/: QZV 解压结果（Emperor 可视化数据）"
echo "   - unweighted_unifrac_pcoa_results_qza/ordination.txt: PCoA 坐标（供 step3_upgma 使用）"
echo ""
