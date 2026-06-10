#!/bin/bash
# step4_taxasummary.sh - 物种组成热图脚本（样本水平）
# 用法：bash step4_taxasummary.sh -i <Relative/> -g <group.list> [--top <N>]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python}"
HEATMAP_DATA_PY="${HEATMAP_DATA_PY:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/heatmapData.py}"
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
HEATMAP_PLOT_R="${HEATMAP_PLOT_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/heatmapPlot.R}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PYTHON_BIN HEATMAP_DATA_PY RSCRIPT_BIN HEATMAP_PLOT_R CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INDIR=""
GROUP_FILE=""
TOP_N="35"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INDIR="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        --top) TOP_N="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_taxasummary.sh -i <Relative/> -g <group.list> [--top <N>]"
            echo ""
            echo "参数:"
            echo "  -i, --input    相对丰度表目录路径"
            echo "  -g, --group    样本分组文件路径"
            echo "  --top          Top 物种数量（默认：35）"
            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INDIR}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ ! -d "${INDIR}" ] && { echo "❌ 错误：相对丰度表目录不存在：${INDIR}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

echo ""
echo "=========================================="
echo "物种组成热图（样本水平）"
echo "=========================================="
echo ""

echo "📊 相对丰度表目录：${INDIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 Top 物种数量：${TOP_N}"
echo ""

# 定义分类层级
LEVELS=("p" "c" "o" "f" "g" "s")
LEVEL_NAMES=("phylum" "class" "order" "family" "genus" "species")

# 创建输出目录
mkdir -p cluster

# 遍历每个分类层级
for i in "${!LEVELS[@]}"; do
    level="${LEVELS[$i]}"
    level_name="${LEVEL_NAMES[$i]}"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 分析 ${level_name} 水平..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Step 1: 生成热图数据
    echo "[1/3] ${level_name}: 生成热图数据..."
    "${PYTHON_BIN}" "${HEATMAP_DATA_PY}" \
        --relative "${INDIR}/asv_table.${level}.relative.xls" \
        --top "${TOP_N}" \
        --level "${level}" \
        --outdir cluster
    
    # Step 2: 绘制热图
    echo "[2/3] ${level_name}: 绘制热图..."
    "${RSCRIPT_BIN}" "${HEATMAP_PLOT_R}" \
        --relative "cluster/cluster.${level}.txt" \
        --taxa "cluster/cluster.${level}__p.list" \
        --level "${level}" \
        --group "${GROUP_FILE}" \
        --outdir cluster
    
    # Step 3: PDF → PNG 转换
    echo "[3/3] ${level_name}: 转换 PDF → PNG..."
    "${CONVERT_BIN}" -density 200 "cluster/cluster.${level}.pdf" "cluster/cluster.${level}.png" 2>/dev/null || true
    
    echo "  ✅ ${level_name} 水平热图完成"
    echo ""
done

echo ""
echo "✅ 物种组成热图（样本水平）完成"
echo ""
echo "📊 输出文件:"
echo "   - cluster/cluster.p.png/pdf: 门水平热图"
echo "   - cluster/cluster.c.png/pdf: 纲水平热图"
echo "   - cluster/cluster.o.png/pdf: 目水平热图"
echo "   - cluster/cluster.f.png/pdf: 科水平热图"
echo "   - cluster/cluster.g.png/pdf: 属水平热图"
echo "   - cluster/cluster.s.png/pdf: 种水平热图"
echo ""
