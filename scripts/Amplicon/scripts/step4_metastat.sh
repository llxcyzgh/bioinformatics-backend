#!/bin/bash
# step4_metastat.sh - MetaStat 组间差异物种分析脚本
# 用法：bash step4_metastat.sh -e <asv_table.even.txt> -g <group.list> -v <Vs.list> [-l <levels>] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"
METASTAT_R="${METASTAT_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/MetaStat1.3.benjamini.R}"
METASTAT_BOXPLOT_PL="${METASTAT_BOXPLOT_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/metastat/metabox/Metastat_boxplot.pl}"
COMPLEX_PL="${COMPLEX_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/brief_report_heatmap/complex.pl}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"

declare -A LEVELS=(
    ["phylum"]="p"
    ["class"]="c"
    ["order"]="o"
    ["family"]="f"
    ["genus"]="g"
    ["species"]="s"
)
ALL_LEVELS=(phylum class order family genus species)

# 解析 -l 参数（支持 phylum,genus 或 p,g；默认全部层级）
_parse_levels() {
    local input="$1"
    local token level
    declare -A seen=()
    SELECTED_LEVELS=()

    if [ -z "${input}" ]; then
        SELECTED_LEVELS=("${ALL_LEVELS[@]}")
        return 0
    fi

    local IFS=','
    for token in ${input}; do
        token="$(echo "${token}" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -z "${token}" ] && continue
        case "${token}" in
            phylum|p) level="phylum" ;;
            class|c) level="class" ;;
            order|o) level="order" ;;
            family|f) level="family" ;;
            genus|g) level="genus" ;;
            species|s) level="species" ;;
            *)
                echo "❌ 错误：未知分类层级：${token}"
                echo "   可选：phylum(p), class(c), order(o), family(f), genus(g), species(s)"
                exit 1
                ;;
        esac
        if [ -z "${seen[$level]}" ]; then
            seen[$level]=1
            SELECTED_LEVELS+=("${level}")
        fi
    done

    if [ ${#SELECTED_LEVELS[@]} -eq 0 ]; then
        echo "❌ 错误：-l 未指定有效分类层级"
        exit 1
    fi
}

# 构建 stat_otu_tab.pl 的 --outsel 参数（如 p,g,s）
_build_outsel() {
    local out=()
    local level
    for level in "${SELECTED_LEVELS[@]}"; do
        out+=("${LEVELS[$level]}")
    done
    local IFS=','
    echo "${out[*]}"
}

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

for bin in RSCRIPT_BIN PERL_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        exit 1
    fi
done
for tool in STAT_OTU_TAB_PL METASTAT_R METASTAT_BOXPLOT_PL COMPLEX_PL COLOR_DEFINED_PL; do
    if [ ! -f "${!tool}" ]; then
        echo "❌ 错误：${tool} 不存在：${!tool}"
        exit 1
    fi
done

EVEN_TABLE=""
GROUP_FILE=""
VS_LIST=""
LEVELS_ARG=""
OUTPUT_DIR=""
SELECTED_LEVELS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--even) EVEN_TABLE="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -v|--vs-list) VS_LIST="$2"; shift 2 ;;
        -l|--levels) LEVELS_ARG="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step4_metastat.sh -e <asv_table.even.txt> -g <group.list> -v <Vs.list> [-l <levels>] -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -e, --even       均一化 ASV 表（step3 输出的 asv_table.even.txt）"
            echo "  -g, --group      分组列表路径"
            echo "  -v, --vs-list    对比组列表路径"
            echo "  -l, --levels     分析层级，逗号分隔（默认全部）"
            echo "                   可选：phylum(p), class(c), order(o), family(f), genus(g), species(s)"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            echo ""
            echo "示例:"
            echo "  -l phylum,genus"
            echo "  -l p,g,s"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${EVEN_TABLE}" ] && { echo "❌ 错误：必须提供 -e asv_table.even.txt"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ -z "${VS_LIST}" ] && { echo "❌ 错误：必须提供 -v"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

_parse_levels "${LEVELS_ARG}"
OUTSEL="$(_build_outsel)"
STAT_OTU_EXTRA=()
if [ ${#SELECTED_LEVELS[@]} -lt ${#ALL_LEVELS[@]} ]; then
    STAT_OTU_EXTRA=(--outsel "${OUTSEL}")
fi

# ----- 路径转绝对路径（cd 输出目录前） -----
EVEN_TABLE="$(abs_path_file "${EVEN_TABLE}")"
GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
VS_LIST="$(abs_path_file "${VS_LIST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

EVENABS_DIR="${OUTPUT_DIR}/Evenabs"
RELATIVE_DIR="${OUTPUT_DIR}/Relative"

echo ""
echo "=========================================="
echo "MetaStat 组间差异物种分析"
echo "=========================================="
echo ""

echo "📊 均一化 ASV 表：${EVEN_TABLE}"
echo "📊 Relative 目录：${RELATIVE_DIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 对比列表：${VS_LIST}"
echo "📊 分析层级：$(IFS=,; echo "${SELECTED_LEVELS[*]}")"
echo ""

# Step 0: 由 group.list 生成 group_col.list（箱线图配色）
echo "[0/6] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

# Step 1-2: 由 asv_table.even.txt 生成 Evenabs / Relative
echo "[1/6] 生成 Evenabs 绝对丰度表..."
"${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
    -unif min \
    "${EVEN_TABLE}" \
    --prefix "${EVENABS_DIR}/asv_table" \
    -nomat -abs \
    "${STAT_OTU_EXTRA[@]}"
echo "  ✅ Evenabs 目录：${EVENABS_DIR}"

echo "[2/6] 生成 Relative 相对丰度表..."
mkdir -p "${RELATIVE_DIR}"
"${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
    "${EVEN_TABLE}" \
    --prefix "${RELATIVE_DIR}/asv_table" \
    "${STAT_OTU_EXTRA[@]}"
echo "  ✅ Relative 目录：${RELATIVE_DIR}"
echo ""

# MetaStat R 一次处理 Evenabs/ 下全部层级文件，自行创建 genus/ phylum/ 等子目录
echo "[3/6] MetaStat 差异分析（R 脚本无终端输出，结果写入各层级目录）..."
"${RSCRIPT_BIN}" "${METASTAT_R}" \
    --threshold 0.05 \
    --infilepath "${EVENABS_DIR}" \
    --group "${GROUP_FILE}" \
    --Vslist "${VS_LIST}" \
    --outdir "./"
echo "  ✅ MetaStat R 分析完成"
echo ""

# 遍历选定分类层级：箱线图 + 热图
for level in "${SELECTED_LEVELS[@]}"; do
    prefix="${LEVELS[$level]}"
    evenabs_file="${EVENABS_DIR}/asv_table.${prefix}.absolute.xls"
    relative_file="${RELATIVE_DIR}/asv_table.${prefix}.relative.xls"

    if [ ! -f "${evenabs_file}" ]; then
        echo "⚠️  跳过 ${level} 水平（Evenabs 无数据：${evenabs_file}）"
        continue
    fi
    if [ ! -f "${relative_file}" ]; then
        echo "❌ 错误：缺少相对丰度表：${relative_file}"
        exit 1
    fi
    if [ ! -d "./${level}" ]; then
        echo "⚠️  跳过 ${level} 水平（MetaStat 未生成 ./${level}/）"
        continue
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 分析 ${level} 水平..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📁 MetaStat 结果：./${level}/"

    echo "[1/2] ${level}: 箱线图绘制..."
    "${PERL_BIN}" "${METASTAT_BOXPLOT_PL}" \
        --mf "${GROUP_FILE}" \
        --vs "${VS_LIST}" \
        --relative "${relative_file}" \
        --colour "${GROUP_COL_LIST}" \
        --prefix "${prefix}" \
        --outdir "./${level}"

    echo "[2/2] ${level}: 差异物种热图..."
    mkdir -p "./${level}/Diff_heatmap"
    cd "./${level}/Diff_heatmap"
    "${PERL_BIN}" "${COMPLEX_PL}" \
        --infile "${relative_file}" \
        --group "${GROUP_FILE}" \
        --top 10 \
        --gene_dir "../" \
        --outdir "."
    cd "${OUTPUT_DIR}"

    date > "./${level}/metastat.fin"
    echo "  ✅ ${level} 水平分析完成"
    echo ""
done

echo ""
echo "✅ MetaStat 组间差异物种分析完成"
echo ""
echo "📊 输出文件:"
echo "   - group_col.list: 分组颜色配置"
echo "   - Evenabs/: 各层级绝对丰度表"
echo "   - Relative/: 各层级相对丰度表"
echo "   - phylum/ ~ species/: 各层级 MetaStat 结果"
echo "   - */Diff_heatmap/: 差异物种热图"
echo ""
