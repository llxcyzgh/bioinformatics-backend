#!/bin/bash
# step4_catecomp.sh - 分类比较统计检验脚本
# 用法：bash step4_catecomp.sh -t <asv_table.even.txt> -g <group.list> [-u <unweighted.dm>] [-w <weighted.dm>]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
CATEGORISE_COMPAIR_PL="${CATEGORISE_COMPAIR_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Categorise_compair/Categorise_compair.pl}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"
TAB_JS_PL="${TAB_JS_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/tab_js.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN CATEGORISE_COMPAIR_PL COLOR_DEFINED_PL TAB_JS_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

ASV_TABLE=""
GROUP_FILE=""
UNWEIGHTED_DM=""
WEIGHTED_DM=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--table) ASV_TABLE="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -u|--unweighted) UNWEIGHTED_DM="$2"; shift 2 ;;
        -w|--weighted) WEIGHTED_DM="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_catecomp.sh -t <asv_table.even.txt> -g <group.list> [-u <unweighted.dm>] [-w <weighted.dm>]"
            echo ""
            echo "参数:"
            echo "  -t, --table       均一化 ASV 表路径"
            echo "  -g, --group       样本分组文件路径"
            echo "  -u, --unweighted  Unweighted UniFrac 距离矩阵路径（可选）"
            echo "  -w, --weighted    Weighted UniFrac 距离矩阵路径（可选）"
            echo "  -h, --help        显示帮助"
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

echo ""
echo "=========================================="
echo "分类比较统计检验"
echo "=========================================="
echo ""

echo "📊 输入文件：${ASV_TABLE}"
echo "📊 分组文件：${GROUP_FILE}"
if [ -n "${UNWEIGHTED_DM}" ] && [ -f "${UNWEIGHTED_DM}" ]; then
    echo "📊 Unweighted UniFrac 距离矩阵：${UNWEIGHTED_DM}"
fi
if [ -n "${WEIGHTED_DM}" ] && [ -f "${WEIGHTED_DM}" ]; then
    echo "📊 Weighted UniFrac 距离矩阵：${WEIGHTED_DM}"
fi
echo ""

# Step 0: 调用 color_defined.pl 生成 group_col.list
echo "[0/5] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"

# Step 1: 执行 Categorise_compair.pl
echo "[1/5] 执行分类比较统计检验..."
"${PERL_BIN}" "${CATEGORISE_COMPAIR_PL}" \
    "${ASV_TABLE}" \
    "${GROUP_FILE}" \
    --group_color "${GROUP_COL_LIST}" \
    "${UNWEIGHTED_DM}" \
    "${WEIGHTED_DM}"

# Step 2-5: 生成各统计方法的 JS 文件
echo "[2/5] 生成 ANOSIM 交互网页..."
if [ -f "Anosim/stat_anosim.txt" ]; then
    "${PERL_BIN}" "${TAB_JS_PL}" "Anosim/stat_anosim.txt" "Anosim/stat_anosim.js"
fi

echo "[3/5] 生成 MRPP 交互网页..."
if [ -f "MRPP/stat_mrpp.txt" ]; then
    "${PERL_BIN}" "${TAB_JS_PL}" "MRPP/stat_mrpp.txt" "MRPP/stat_mrpp.js"
fi

echo "[4/5] 生成 Adonis 交互网页..."
if [ -f "Adonis/bray_adonis.txt" ]; then
    "${PERL_BIN}" "${TAB_JS_PL}" "Adonis/bray_adonis.txt" "Adonis/stat_adonis.js"
fi

echo "[5/5] 生成 AMOVA 交互网页..."
if [ -f "Amova/weighted_unifrac/stat_amova.txt" ]; then
    "${PERL_BIN}" "${TAB_JS_PL}" "Amova/weighted_unifrac/stat_amova.txt" "Amova/weighted_unifrac/stat_amova.js"
fi

echo ""
echo "✅ 分类比较统计检验完成"
echo ""
echo "📊 输出文件:"
echo "   - Anosim/stat_anosim.txt: ANOSIM 统计结果"
echo "   - MRPP/stat_mrpp.txt: MRPP 统计结果"
if [ -f "Adonis/bray_adonis.txt" ]; then
    echo "   - Adonis/bray_adonis.txt: Adonis 统计结果"
fi
if [ -f "Amova/weighted_unifrac/stat_amova.txt" ]; then
    echo "   - Amova/weighted_unifrac/stat_amova.txt: AMOVA 统计结果"
fi
echo ""
