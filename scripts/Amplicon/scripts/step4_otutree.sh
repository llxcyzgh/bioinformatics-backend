#!/bin/bash
# step4_otutree.sh - OTU 树可视化脚本
# 用法：bash step4_otutree.sh -t <upgma_tree.tre> -r <top10_asv_table.p.relative.xls>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
DRAW_TREE_PL="${DRAW_TREE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/draw_tree.pl}"
SVG2XXX_BIN="${SVG2XXX_BIN:-/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN DRAW_TREE_PL SVG2XXX_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

TREE_FILE=""
RELATIVE_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tree) TREE_FILE="$2"; shift 2 ;;
        -r|--relative) RELATIVE_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_otutree.sh -t <upgma_tree.tre> -r <top10_asv_table.p.relative.xls>"
            echo ""
            echo "参数:"
            echo "  -t, --tree       UPGMA 树文件路径"
            echo "  -r, --relative   Top10 物种丰度表路径"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${TREE_FILE}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${RELATIVE_FILE}" ] && { echo "❌ 错误：必须提供 -r"; exit 1; }
[ ! -f "${TREE_FILE}" ] && { echo "❌ 错误：树文件不存在：${TREE_FILE}"; exit 1; }
[ ! -f "${RELATIVE_FILE}" ] && { echo "❌ 错误：丰度表不存在：${RELATIVE_FILE}"; exit 1; }

echo ""
echo "=========================================="
echo "OTU 树可视化"
echo "=========================================="
echo ""

echo "🌳 UPGMA 树：${TREE_FILE}"
echo "📊 Top10 丰度表：${RELATIVE_FILE}"
echo ""

# Step 1: 绘制 Weighted UniFrac 树
echo "[1/4] 绘制 Weighted UniFrac 树..."
"${PERL_BIN}" "${DRAW_TREE_PL}" \
    "${TREE_FILE}" \
    "${RELATIVE_FILE}" \
    --trantab \
    -bun 0.25,4 \
    -bline \
    -btitle 'Relative Abundance in Phylum Level' \
    --scal_title 'Weighted Unifrac Distance' \
    -width 200 \
    -type 3 > UPGMA.W.tree.svg

# Step 2: SVG → PNG 转换
echo "[2/4] 转换 Weighted 树 SVG → PNG..."
"${SVG2XXX_BIN}" UPGMA.W.tree.svg -t png

# Step 3: 绘制 Unweighted UniFrac 树
echo "[3/4] 绘制 Unweighted UniFrac 树..."
"${PERL_BIN}" "${DRAW_TREE_PL}" \
    "${TREE_FILE}" \
    "${RELATIVE_FILE}" \
    --trantab \
    -bun 0.25,4 \
    -bline \
    -btitle 'Relative Abundance in Phylum Level' \
    --scal_title 'Unweighted Unifrac Distance' \
    -width 200 \
    -type 3 > UPGMA.UnW.tree.svg

# Step 4: SVG → PNG 转换
echo "[4/4] 转换 Unweighted 树 SVG → PNG..."
"${SVG2XXX_BIN}" UPGMA.UnW.tree.svg -t png

echo ""
echo "✅ OTU 树可视化完成"
echo ""
echo "📊 输出文件:"
echo "   - UPGMA.W.tree.svg: Weighted UniFrac 树（SVG）"
echo "   - UPGMA.W.tree.png: Weighted UniFrac 树（PNG）"
echo "   - UPGMA.UnW.tree.svg: Unweighted UniFrac 树（SVG）"
echo "   - UPGMA.UnW.tree.png: Unweighted UniFrac 树（PNG）"
echo ""
