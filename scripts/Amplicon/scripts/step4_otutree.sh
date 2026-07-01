#!/bin/bash
# step4_otutree.sh - OTU 树可视化脚本
# 用法：bash step4_otutree.sh -w <weighted_upgma.tre> -u <unweighted_upgma.tre> -r <top10_p.relative.xls> [-g group.list] -o <output_dir>
# 样本与分组共用同一套参数，传入 step3_upgma 样本/分组 .tre 及 step3_top_species 对应 Top10 表即可

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
DRAW_TREE_PL="${DRAW_TREE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/draw_tree.pl}"
SVG2XXX_BIN="${SVG2XXX_BIN:-/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx}"

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -x "${PERL_BIN}" ]; then
    echo "❌ 错误：PERL_BIN 不存在：${PERL_BIN}"
    exit 1
fi
for bin in DRAW_TREE_PL SVG2XXX_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

WEIGHTED_TREE=""
UNWEIGHTED_TREE=""
RELATIVE_FILE=""
GROUP_LIST=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--weighted-tree) WEIGHTED_TREE="$2"; shift 2 ;;
        -u|--unweighted-tree) UNWEIGHTED_TREE="$2"; shift 2 ;;
        -r|--relative) RELATIVE_FILE="$2"; shift 2 ;;
        -g|--group) GROUP_LIST="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            cat <<'EOF'
用法：bash step4_otutree.sh -w <weighted.tre> -u <unweighted.tre> -r <top10_p.xls> [-g group.list] -o <output_dir>

参数:
  -w, --weighted-tree     Weighted UniFrac UPGMA 树（step3_upgma 产出）
  -u, --unweighted-tree   Unweighted UniFrac UPGMA 树（step3_upgma 产出）
  -r, --relative          门水平 Top10 物种丰度表（step3_top_species 产出）
  -g, --group             样本分组文件（可选，传给 draw_tree.pl --group 着色）
  -o, --output            输出目录
  -h, --help              显示帮助

样本示例（-o 建议 OTUTree_sample/）:
  -w UPGMA/UPGMA_sample/unrarefied_bdiv/asv_table.even_weighted_unifrac_upgma.tre
  -u UPGMA/UPGMA_sample/unrarefied_bdiv/asv_table.even_unweighted_unifrac_upgma.tre
  -r TopSpecies/top10/asv_table.p10.relative.xls

分组示例（需 step3_upgma -G、step3_top_species -g，-o 建议 OTUTree_group/）:
  -w UPGMA/UPGMA_group/unrarefied_bdiv/asv_table.group.even_weighted_unifrac_upgma.tre
  -u UPGMA/UPGMA_group/unrarefied_bdiv/asv_table.group.even_unweighted_unifrac_upgma.tre
  -r TopSpecies/top10_group/asv_table.p10.group.relative.xls
EOF
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

if [ -z "${WEIGHTED_TREE}" ]; then echo "❌ 错误：必须提供 -w（Weighted UPGMA 树）"; exit 1; fi
if [ -z "${UNWEIGHTED_TREE}" ]; then echo "❌ 错误：必须提供 -u（Unweighted UPGMA 树）"; exit 1; fi
if [ -z "${RELATIVE_FILE}" ]; then echo "❌ 错误：必须提供 -r"; exit 1; fi
if [ ! -f "${WEIGHTED_TREE}" ]; then echo "❌ 错误：Weighted 树不存在：${WEIGHTED_TREE}"; exit 1; fi
if [ ! -f "${UNWEIGHTED_TREE}" ]; then echo "❌ 错误：Unweighted 树不存在：${UNWEIGHTED_TREE}"; exit 1; fi
if [ ! -f "${RELATIVE_FILE}" ]; then echo "❌ 错误：丰度表不存在：${RELATIVE_FILE}"; exit 1; fi
if [ -n "${GROUP_LIST}" ] && [ ! -f "${GROUP_LIST}" ]; then echo "❌ 错误：分组文件不存在：${GROUP_LIST}"; exit 1; fi
if [ -z "${OUTPUT_DIR}" ]; then echo "❌ 错误：必须提供 -o"; exit 1; fi

WEIGHTED_TREE="$(abs_path_file "${WEIGHTED_TREE}")"
UNWEIGHTED_TREE="$(abs_path_file "${UNWEIGHTED_TREE}")"
RELATIVE_FILE="$(abs_path_file "${RELATIVE_FILE}")"
GROUP_LIST="$(abs_path_file_optional "${GROUP_LIST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

draw_otu_tree() {
    local tree_file="$1"
    local svg_out="$2"
    local scale_title="$3"

    local draw_args=(
        "${DRAW_TREE_PL}"
        "${tree_file}"
        "${RELATIVE_FILE}"
        --trantab
        -bun 0.25,4
        -bline
        -btitle 'Relative Abundance in Phylum Level'
        --scal_title "${scale_title}"
        -width 200
        -type 3
    )
    if [ -n "${GROUP_LIST}" ]; then
        draw_args+=(--group "${GROUP_LIST}")
    fi

    "${PERL_BIN}" "${draw_args[@]}" > "${svg_out}"
    "${SVG2XXX_BIN}" "${svg_out}" -t png
}

echo ""
echo "=========================================="
echo "OTU 树可视化"
echo "=========================================="
echo ""

echo "🌳 Weighted UPGMA 树：${WEIGHTED_TREE}"
echo "🌳 Unweighted UPGMA 树：${UNWEIGHTED_TREE}"
echo "📊 Top10 丰度表：${RELATIVE_FILE}"
if [ -n "${GROUP_LIST}" ]; then
    echo "📊 分组文件：${GROUP_LIST}"
fi
echo ""

echo "[1/4] 绘制 Weighted UniFrac 树..."
draw_otu_tree "${WEIGHTED_TREE}" "UPGMA.W.tree.svg" "Weighted Unifrac Distance"

echo "[2/4] 绘制 Unweighted UniFrac 树..."
draw_otu_tree "${UNWEIGHTED_TREE}" "UPGMA.UnW.tree.svg" "Unweighted Unifrac Distance"

echo "[3/4] 完成 SVG → PNG 转换"
echo "[4/4] 输出整理完成"

echo ""
echo "✅ OTU 树可视化完成"
echo ""
echo "📊 输出文件:"
echo "   - UPGMA.W.tree.svg / UPGMA.W.tree.png"
echo "   - UPGMA.UnW.tree.svg / UPGMA.UnW.tree.png"
echo ""
