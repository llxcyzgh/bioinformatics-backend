#!/bin/bash
# step3_alpha_data.sh - Alpha 多样性指数计算脚本
# 用法：bash step3_alpha_data.sh -i <asv_table.even.txt> [-t rooted-tree.qza] [-m alpha.mf] -o <output_dir>

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

EVEN_TABLE=""
TREE_FILE=""
META_FILE=""

OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) EVEN_TABLE="$2"; shift 2 ;;
        -t|--tree) TREE_FILE="$2"; shift 2 ;;
        -m|--meta) META_FILE="$2"; shift 2 ;;
                -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step3_alpha_data.sh -i <asv_table.even.txt> [-t rooted-tree.qza] [-m alpha.mf]"
            echo ""
            echo "参数:"
            echo "  -i, --input      均一化 ASV 表路径"
            echo "  -t, --tree       有根系统发育树路径（可选，用于稀化曲线）"
            echo "  -m, --meta       样本元数据文件路径（可选，用于稀化曲线；需含 #SampleID、Description 表头，缺失时自动补全）"
            echo "  -o, --output     输出目录"

            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
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
echo "Alpha 多样性指数计算"
echo "=========================================="
echo ""

echo "📊 输入文件：${EVEN_TABLE}"
if [ -n "${TREE_FILE}" ] && [ -f "${TREE_FILE}" ]; then
    echo "📊 系统发育树：${TREE_FILE}"
fi
if [ -n "${META_FILE}" ] && [ -f "${META_FILE}" ]; then
    echo "📊 样本元数据：${META_FILE}"
fi
echo ""

# 激活 conda 环境
source "${CONDA_BIN}/activate" "${CONDA_ENV}"

# Step 1: BIOM 转换
echo "[1/5] BIOM 转换..."
biom convert \
    -i "${EVEN_TABLE}" \
    -o asv_table.even.biom \
    --to-json \
    --table-type="OTU table"

# Step 2: 导入 QIIME2
echo "[2/5] 导入 QIIME2..."
qiime tools import \
    --input-path asv_table.even.biom \
    --type 'FeatureTable[Frequency]' \
    --input-format BIOMV100Format \
    --output-path asv_table.even.qza

# Step 3: 计算 Alpha 指数
echo "[3/5] 计算 Alpha 指数..."
mkdir -p alpha_index_table

for index in chao1 shannon simpson observed_features goods_coverage dominance pielou_e; do
    echo "  计算 ${index}..."
    qiime diversity alpha \
        --i-table asv_table.even.qza \
        --p-metric ${index} \
        --o-alpha-diversity alpha_index_table/${index}.qza
    
    # 导出结果
    qiime tools export \
        --input-path alpha_index_table/${index}.qza \
        --output-path alpha_index_table/${index}_qza
done

# Step 4: 合并指数表
echo "[4/5] 合并指数表..."
echo -e "Sample_Name\tchao1\tdominance\tgoods_coverage\tobserved_features\tpielou_e\tshannon\tsimpson" > alpha_index_table/alpha_diversity_index.txt
paste alpha_index_table/*_qza/* | awk -F"\t" '{if(!(NR==1)){printf ("%s\t%.3f\t%.3f\t%.3f\t%s\t%.3f\t%.3f\t%.3f\n",$1,$2,$4,$6,$8,$10,$12,$14)}}' >> alpha_index_table/alpha_diversity_index.txt

# Step 5: Alpha 稀化曲线（可选）
if [ -n "${TREE_FILE}" ] && [ -f "${TREE_FILE}" ] && [ -n "${META_FILE}" ] && [ -f "${META_FILE}" ]; then
    echo "[5/5] Alpha 稀化曲线..."

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
    
    # 自动计算最大深度
    MAX_DEPTH=$(qiime tools export \
        --input-path asv_table.even.qza \
        --output-path asv_table_even_export 2>/dev/null && \
        cat asv_table_even_export/*.tsv | tail -n +2 | awk -F'\t' '{sum=0; for(i=2;i<=NF;i++) sum+=$i; print sum}' | sort -n | sed '/^0/d' | sed -n '1p')
    
    if [ -z "${MAX_DEPTH}" ] || [ "${MAX_DEPTH}" -lt 10 ]; then
        MAX_DEPTH=1000
    fi
    
    qiime diversity alpha-rarefaction \
        --i-table asv_table.even.qza \
        --i-phylogeny "${TREE_FILE}" \
        --p-min-depth 10 \
        --p-max-depth ${MAX_DEPTH} \
        --m-metadata-file "${META_FILE_QIIME}" \
        --p-metrics chao1 \
        --p-metrics observed_features \
        --p-metrics goods_coverage \
        --p-metrics shannon \
        --p-metrics simpson \
        --p-metrics dominance \
        --p-metrics pielou_e \
        --o-visualization alpha_rarefaction.qzv
    
    # 导出稀化曲线数据
    qiime tools export \
        --input-path alpha_rarefaction.qzv \
        --output-path alpha_rarefaction_qzv
else
    echo "⚠️  跳过稀化曲线（未提供 tree 或 meta 文件）"
fi

# 清理临时文件
rm -f asv_table.even.biom
rm -rf asv_table_even_export

echo ""
echo "✅ Alpha 多样性指数计算完成"
echo ""
echo "📊 输出文件:"
echo "   - alpha_index_table/chao1.qza: Chao1 丰富度"
echo "   - alpha_index_table/shannon.qza: Shannon 多样性"
echo "   - alpha_index_table/simpson.qza: Simpson 多样性"
echo "   - alpha_index_table/observed_features.qza: 观测物种数"
echo "   - alpha_index_table/goods_coverage.qza: Goods 覆盖度"
echo "   - alpha_index_table/dominance.qza: Simpson 优势度"
echo "   - alpha_index_table/pielou_e.qza: Pielou 均匀度"
echo "   - alpha_index_table/alpha_diversity_index.txt: 综合指数表"
if [ -f "alpha_rarefaction.qzv" ]; then
    echo "   - alpha_rarefaction.qzv: Alpha 稀化曲线"
fi
echo ""
