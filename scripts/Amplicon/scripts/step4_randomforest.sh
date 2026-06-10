#!/bin/bash
# step4_randomforest.sh - 随机森林分析脚本
# 用法：bash step4_randomforest.sh -i <Relative/> -g <group.list> -r <rf.list>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
RF_ROC_PL="${RF_ROC_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/rf_roc/rf_roc.pl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN RF_ROC_PL CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INDIR=""
GROUP_FILE=""
RF_LIST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--indir) INDIR="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -r|--rf-list) RF_LIST="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_randomforest.sh -i <Relative/> -g <group.list> -r <rf.list>"
            echo ""
            echo "参数:"
            echo "  -i, --indir     相对丰度表目录路径"
            echo "  -g, --group     样本分组文件路径"
            echo "  -r, --rf-list   Random Forest 对比列表路径"
            echo "  -h, --help      显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INDIR}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ -z "${RF_LIST}" ] && { echo "❌ 错误：必须提供 -r"; exit 1; }
[ ! -d "${INDIR}" ] && { echo "❌ 错误：相对丰度表目录不存在：${INDIR}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }
[ ! -f "${RF_LIST}" ] && { echo "❌ 错误：对比列表不存在：${RF_LIST}"; exit 1; }

echo ""
echo "=========================================="
echo "随机森林分析"
echo "=========================================="
echo ""

echo "📊 相对丰度表目录：${INDIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 对比列表：${RF_LIST}"
echo ""

# Step 1: 执行随机森林分析
echo "[1/2] 执行随机森林 + ROC 曲线分析..."
"${PERL_BIN}" "${RF_ROC_PL}" \
    --rf "${RF_LIST}" \
    --indir "${INDIR}" \
    --rank p,c,o,f,g,s,otu \
    --group "${GROUP_FILE}" \
    --outdir ./

# Step 2: 合并图片
echo "[2/2] 合并重要性图和 AUC 曲线..."

# 合并重要性图
"${CONVERT_BIN}" +append \
    genus/1*/30/impplot_MeanDecreaseAccuracy30.png \
    genus/1_*/30/impplot_MeanDecreaseGin30.png \
    tax_show_ea.png 2>/dev/null || true

"${CONVERT_BIN}" +append \
    genus/1*/30/impplot_MeanDecreaseAccuracy30.pdf \
    genus/1_*/30/impplot_MeanDecreaseGin30.pdf \
    tax_show_ea.pdf 2>/dev/null || true

# 合并 AUC 曲线
"${CONVERT_BIN}" +append \
    genus/1_*/trainset_auc.png \
    genus/1_H_vs_D/testset_auc.png \
    auc.png 2>/dev/null || true

"${CONVERT_BIN}" +append \
    genus/1_*/trainset_auc.pdf \
    genus/1_*/testset_auc.pdf \
    auc.pdf 2>/dev/null || true

echo ""
echo "✅ 随机森林分析完成"
echo ""
echo "📊 输出文件:"
echo "   - genus/impplot_MeanDecreaseAccuracy*.png/pdf: 重要性图（准确率）"
echo "   - genus/impplot_MeanDecreaseGini*.png/pdf: 重要性图（基尼系数）"
echo "   - genus/trainset_auc.png/pdf: 训练集 AUC 曲线"
echo "   - genus/testset_auc.png/pdf: 测试集 AUC 曲线"
echo "   - tax_show_ea.png/pdf: 重要性图合并图"
echo "   - auc.png/pdf: AUC 曲线合并图"
echo ""
