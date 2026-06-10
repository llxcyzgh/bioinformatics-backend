#!/bin/bash
# step5_pca_pcoa.sh - PCA/PCoA 排序分析脚本
# 用法：bash step5_pca_pcoa.sh -r <relative_table> -g <group_col> -wu <unweighted_pc> -w <weighted_pc> -o <output_dir>

set -e

RELATIVE_TABLE=""
GROUP_COL=""
UNWEIGHTED_PC=""
WEIGHTED_PC=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--relative) RELATIVE_TABLE="$2"; shift 2 ;;
        -g|--group-col) GROUP_COL="$2"; shift 2 ;;
        -wu|--unweighted-pc) UNWEIGHTED_PC="$2"; shift 2 ;;
        -w|--weighted-pc) WEIGHTED_PC="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step5_pca_pcoa.sh -r <table> -g <col> -o <output>"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

mkdir -p "${OUTPUT_DIR}"/{PCA,PCoA/PCoA/{weighted_unifrac,unweighted_unifrac},PCoA/Unifrac_heatmap}

echo ""
echo "=========================================="
echo "PCA/PCoA 排序分析"
echo "=========================================="
echo ""

if [ -n "${RELATIVE_TABLE}" ] && [ -n "${GROUP_COL}" ]; then
    echo "📊 执行 PCA 分析..."
    Rscript /newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCA/UOA.R \
        --rFile "${RELATIVE_TABLE}" --gcFile "${GROUP_COL}" --method pca --workdir "${OUTPUT_DIR}/PCA"
fi

if [ -n "${WEIGHTED_PC}" ] && [ -n "${UNWEIGHTED_PC}" ]; then
    echo "📊 绘制 PCoA 图..."
    Rscript /newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCoA/plot_PCoA.R \
        --unifrac_pc "${WEIGHTED_PC}" --group_col "${GROUP_COL}" --outdir "${OUTPUT_DIR}/PCoA/PCoA/weighted_unifrac"
    
    Rscript /newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCoA/plot_PCoA.R \
        --unifrac_pc "${UNWEIGHTED_PC}" --group_col "${GROUP_COL}" --outdir "${OUTPUT_DIR}/PCoA/PCoA/unweighted_unifrac"
    
    /usr/bin/convert +append "${OUTPUT_DIR}/PCoA/PCoA/weighted_unifrac/PCoA12.pdf" "${OUTPUT_DIR}/PCoA/PCoA/unweighted_unifrac/PCoA12.pdf" "${OUTPUT_DIR}/PCoA/PCoA/PCoA.pdf"
    /usr/bin/convert +append "${OUTPUT_DIR}/PCoA/PCoA/weighted_unifrac/PCoA12.png" "${OUTPUT_DIR}/PCoA/PCoA/unweighted_unifrac/PCoA12.png" "${OUTPUT_DIR}/PCoA/PCoA/PCoA.png"
fi

echo "✅ PCA/PCoA 排序分析完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - PCA/UOA_pca.png: PCA 排序图"
echo "   - PCoA/PCoA/PCoA.png: PCoA 合并图"
echo ""
