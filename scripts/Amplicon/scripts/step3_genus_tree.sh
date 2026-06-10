#!/bin/bash
# step3_genus_tree.sh - 属水平进化树脚本
# 用法：bash step3_genus_tree.sh -t <taxonomy> -g <genus_table> -s <asv_seqs> -o <output_dir>

set -e

TAXONOMY=""
GENUS_TABLE=""
ASV_SEQS=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--taxonomy) TAXONOMY="$2"; shift 2 ;;
        -g|--genus-table) GENUS_TABLE="$2"; shift 2 ;;
        -s|--asv-seqs) ASV_SEQS="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_genus_tree.sh -t <taxonomy> -g <genus> -s <seqs> -o <output>"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${TAXONOMY}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

mkdir -p "${OUTPUT_DIR}"/{genus_evolutionary_tree,genus_evolutionary_tree_group}
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "属水平进化树构建"
echo "=========================================="
echo ""

echo "🔬 筛选 Top 属及其 OTU/ASV..."
perl /newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/../00.Commbin/test_bin/select_OTUs.pl \
    "${TAXONOMY}" "${GENUS_TABLE}" \
    --sprefix g__ -full --top 100 \
    --otutab "${GENUS_TABLE}" \
    --outdir selOTUs/

echo "🧬 准备属序列..."
cd genus_evolutionary_tree
perl /newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/lib/make_genus_table.pl \
    "${GENUS_TABLE}" "${ASV_SEQS}" \
    preselected_genus.fasta phylum.list 100

echo "🔬 多序列比对..."
source /gfs/users/guorongjun/miniconda3/bin/activate qiime1
align_seqs.py -i selected_genus.fasta -m muscle

echo "🌳 构建进化树..."
make_phylogeny.py -i muscle_aligned/selected_genus_aligned.fasta -o genus_100.tree

echo ""
echo "✅ 属水平进化树构建完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - genus_evolutionary_tree/genus_100.tree.png: 样本属进化树"
echo "   - genus_evolutionary_tree_group/genus_group_100.tree.png: 分组属进化树"
echo ""
