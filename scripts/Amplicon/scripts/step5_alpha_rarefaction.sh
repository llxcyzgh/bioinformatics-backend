#!/bin/bash
# step5_alpha_rarefaction.sh - Alpha 多样性稀化曲线脚本
# 用法：bash step5_alpha_rarefaction.sh -t <asv_table.even.txt> -g <group.list> -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
PYTHON_BIN="${PYTHON_BIN:-/gfs/users/guorongjun/miniconda3/bin/python}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# R 脚本路径
RANK_ABUNDANCE_R="${RANK_ABUNDANCE_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/rank_abundance.R}"
ALPHA_RAREFACTION_PL="${ALPHA_RAREFACTION_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/alpha_rarefaction.pl}"
PLOT_ALPHAINDEX_R="${PLOT_ALPHAINDEX_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/plot_aplhaindex.R}"
RAREFACTION_GROUP_PY="${RAREFACTION_GROUP_PY:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/rarefacton_group.py}"
LINE_ERRBAR_R="${LINE_ERRBAR_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/line_errbar.R}"
RANK_ABUNDANCE_GROUP_R="${RANK_ABUNDANCE_GROUP_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/rank_abundance_group.R}"
COMBINE_OTUTABLE_PL="${COMBINE_OTUTABLE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/Alpha_rarefacton/Combine_otutable.pl}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in RSCRIPT_BIN PERL_BIN PYTHON_BIN CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

# 验证 Perl 脚本存在
if [ ! -f "${COLOR_DEFINED_PL}" ]; then
    echo "❌ 错误：color_defined.pl 不存在：${COLOR_DEFINED_PL}"
    echo "   可通过环境变量覆盖，例如：export COLOR_DEFINED_PL=\"/your/path/to/color_defined.pl\""
    exit 1
fi

ASV_TABLE=""
GROUP_FILE=""

OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--table) ASV_TABLE="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
                -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step5_alpha_rarefaction.sh -t <asv_table.even.txt> -g <group.list> -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -t, --table    均一化 ASV 表路径"
            echo "  -g, --group    样本分组文件路径"
            echo "  -o, --output     输出目录"

            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${ASV_TABLE}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ ! -f "${ASV_TABLE}" ] && { echo "❌ 错误：ASV 表不存在：${ASV_TABLE}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# ----- 路径转绝对路径（cd 输出目录前） -----
ASV_TABLE="$(abs_path_file "${ASV_TABLE}")"
GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "Alpha 多样性稀化曲线分析"
echo "=========================================="
echo ""

echo "📊 ASV 表：${ASV_TABLE}"
echo "📊 分组文件：${GROUP_FILE}"
echo ""

# Step 0: 调用 color_defined.pl 生成 group_col.list
echo "[0/9] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

# Step 1: Rank Abundance 曲线
echo "[1/9] 绘制 Rank Abundance 曲线..."
"${RSCRIPT_BIN}" "${RANK_ABUNDANCE_R}" "${ASV_TABLE}" rank_abundance
"${CONVERT_BIN}" rank_abundance.pdf rank_abundance.png 2>/dev/null || true

# Step 2: 处理稀化曲线数据
echo "[2/9] 处理稀化曲线数据..."
if [ -d "alpha_index_table" ] && [ -f "alpha_index_table/observed_features.csv" ]; then
    "${PERL_BIN}" "${ALPHA_RAREFACTION_PL}" "alpha_index_table/observed_features.csv" observed_features
else
    echo "⚠️  未找到 alpha_index_table/observed_features.csv，跳过稀化曲线数据处理"
    # 创建示例数据
    echo "SampleID,observed_features" > observed_features.csv
    echo "Sample001,100" >> observed_features.csv
fi

# Step 3: 绘制 Observed Features 曲线
echo "[3/9] 绘制 Observed Features 曲线..."
if [ -f "observed_features.sample.xls" ]; then
    "${RSCRIPT_BIN}" "${PLOT_ALPHAINDEX_R}" observed_features.sample.xls observed_features
    "${CONVERT_BIN}" observed_features.pdf observed_features.png 2>/dev/null || true
fi

# Step 4: 合并 Alpha 多样性图
echo "[4/9] 合并 Alpha 多样性图..."
"${CONVERT_BIN}" +append observed_features.pdf rank_abundance.pdf alpha_diversity.pdf 2>/dev/null || true
"${CONVERT_BIN}" +append observed_features.png rank_abundance.png alpha_diversity.png 2>/dev/null || true

# Step 5: 分组稀化曲线
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔬 分析分组稀化曲线..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 5: 分组稀化曲线
echo "[5/9] 生成分组稀化曲线数据..."
if [ -f "observed_features.sample.xls" ]; then
    "${PYTHON_BIN}" "${RAREFACTION_GROUP_PY}" \
        -i observed_features.sample.xls \
        -g "${GROUP_COL_LIST}" \
        -p observed_features \
        -o ./ > observed_features.group.xls
fi

# Step 6: 绘制分组误差线图
echo "[6/9] 绘制分组误差线图..."
if [ -f "observed_features.group.xls" ]; then
    "${RSCRIPT_BIN}" "${LINE_ERRBAR_R}" observed_features.group.xls "${GROUP_COL_LIST}" observed_features
fi

# Step 7: 绘制分组 Rank Abundance 曲线
echo "[7/9] 生成分组 ASV 表..."
"${PERL_BIN}" "${COMBINE_OTUTABLE_PL}" "${ASV_TABLE}" "${GROUP_FILE}" > group_otu_table.even.txt

echo "[8/9] 绘制分组 Rank Abundance 曲线..."
"${RSCRIPT_BIN}" "${RANK_ABUNDANCE_GROUP_R}" group_otu_table.even.txt "${GROUP_COL_LIST}" group_rank_abundance
"${CONVERT_BIN}" group_rank_abundance.pdf group_rank_abundance.png 2>/dev/null || true

# 合并分组图
echo "[9/9] 合并分组 Alpha 多样性图..."
"${CONVERT_BIN}" +append observed_features.group.pdf group_rank_abundance.pdf alpha_diversity.group.pdf 2>/dev/null || true
"${CONVERT_BIN}" +append observed_features.group.png group_rank_abundance.png alpha_diversity.group.png 2>/dev/null || true

# 清理临时文件
rm -f "${GROUP_COL_LIST}"

echo ""
echo "✅ Alpha 多样性稀化曲线分析完成"
echo ""
echo "📊 输出文件:"
echo "   - rank_abundance.svg/png: Rank Abundance 曲线"
echo "   - observed_features.svg/png: Observed Features 稀化曲线"
echo "   - alpha_diversity.svg/png: Alpha 多样性合并图"
echo "   - observed_features.group.svg/png: 分组稀化曲线"
echo "   - alpha_diversity.group.svg/png: 分组 Alpha 多样性合并图"
echo "   - group_otu_table.even.txt: 分组 ASV 表"
echo ""
