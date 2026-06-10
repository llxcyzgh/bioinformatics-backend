#!/bin/bash
# step4_metastat.sh - MetaStat 组间差异物种分析脚本
# 用法：bash step4_metastat.sh -e <evenabs/> -g <group.list> -v <Vs.list>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
METASTAT_R="${METASTAT_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/MetaStat1.3.benjamini.R}"
METASTAT_BOXPLOT_PL="${METASTAT_BOXPLOT_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/metabox/Metastat_boxplot.pl}"
COMPLEX_PL="${COMPLEX_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/brief_report_heatmap/complex.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in RSCRIPT_BIN METASTAT_R METASTAT_BOXPLOT_PL COMPLEX_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

EVENABS_DIR=""
GROUP_FILE=""
VS_LIST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--evenabs) EVENABS_DIR="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -v|--vs-list) VS_LIST="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_metastat.sh -e <evenabs/> -g <group.list> -v <Vs.list>"
            echo ""
            echo "参数:"
            echo "  -e, --evenabs    均一化绝对丰度表目录"
            echo "  -g, --group      分组列表路径"
            echo "  -v, --vs-list    对比组列表路径"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${EVENABS_DIR}" ] && { echo "❌ 错误：必须提供 -e"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ -z "${VS_LIST}" ] && { echo "❌ 错误：必须提供 -v"; exit 1; }
[ ! -d "${EVENABS_DIR}" ] && { echo "❌ 错误：evenabs 目录不存在：${EVENABS_DIR}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }
[ ! -f "${VS_LIST}" ] && { echo "❌ 错误：对比列表不存在：${VS_LIST}"; exit 1; }

echo ""
echo "=========================================="
echo "MetaStat 组间差异物种分析"
echo "=========================================="
echo ""

echo "📊 均一化绝对丰度表目录：${EVENABS_DIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 对比列表：${VS_LIST}"
echo ""

# 定义分析层级
declare -A LEVELS=(
    ["phylum"]="p"
    ["class"]="c"
    ["order"]="o"
    ["family"]="f"
    ["genus"]="g"
    ["species"]="s"
)

# 遍历每个分类层级
for level in "${!LEVELS[@]}"; do
    prefix="${LEVELS[$level]}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 分析 ${level} 水平..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Step 1: MetaStat R 分析
    echo "[1/3] ${level}: MetaStat 差异分析..."
    "${RSCRIPT_BIN}" "${METASTAT_R}" \
        --threshold 0.05 \
        --infilepath "${EVENABS_DIR}/${level}" \
        --group "${GROUP_FILE}" \
        --Vslist "${VS_LIST}" \
        --outdir "./${level}"
    
    # Step 2: 箱线图绘制
    echo "[2/3] ${level}: 箱线图绘制..."
    "${PERL_BIN}" "${METASTAT_BOXPLOT_PL}" \
        --mf "${GROUP_FILE}" \
        --vs "${VS_LIST}" \
        --relative "${EVENABS_DIR}/../Relative/asv_table.${prefix}.relative.xls" \
        --colour "group_col.list" \
        --prefix "${prefix}" \
        --outdir "./${level}"
    
    # Step 3: 差异物种热图
    echo "[3/3] ${level}: 差异物种热图..."
    mkdir -p "./${level}/Diff_heatmap"
    cd "./${level}/Diff_heatmap"
    "${PERL_BIN}" "${COMPLEX_PL}" \
        --infile "${EVENABS_DIR}/../Relative/asv_table.${prefix}.relative.xls" \
        --group "${GROUP_FILE}" \
        --top 10 \
        --gene_dir "../"
    cd ..
    
    # 完成标记
    date > "./${level}/metastat.fin"
    
    echo "  ✅ ${level} 水平分析完成"
    echo ""
done

echo ""
echo "✅ MetaStat 组间差异物种分析完成"
echo ""
echo "📊 输出文件:"
echo "   - phylum/: 门水平分析结果"
echo "   - class/: 纲水平分析结果"
echo "   - order/: 目水平分析结果"
echo "   - family/: 科水平分析结果"
echo "   - genus/: 属水平分析结果"
echo "   - species/: 种水平分析结果"
echo "   - */Diff_heatmap/: 差异物种热图"
echo ""
