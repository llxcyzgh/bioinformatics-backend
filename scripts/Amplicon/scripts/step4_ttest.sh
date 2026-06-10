#!/bin/bash
# step4_ttest.sh - T 检验与 Wilcoxon 检验脚本
# 用法：bash step4_ttest.sh -i <Relative/> -g <group.list> [--threshold <P 值>] [--method <t|wilcox>]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
GET_T_WILCOX_PL="${GET_T_WILCOX_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/t.wilcox.R.lib/get.t.wilcox.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN GET_T_WILCOX_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INDIR=""
GROUP_FILE=""
THRESHOLD="0.05"
METHOD="t"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INDIR="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        --threshold) THRESHOLD="$2"; shift 2 ;;
        --method) METHOD="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_ttest.sh -i <Relative/> -g <group.list> [--threshold <P 值>] [--method <t|wilcox>]"
            echo ""
            echo "参数:"
            echo "  -i, --input      相对丰度表目录路径"
            echo "  -g, --group      样本分组文件路径"
            echo "  --threshold      P 值阈值（默认：0.05）"
            echo "  --method         检验方法：t 或 wilcox（默认：t）"
            echo "  -h, --help       显示帮助"
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
echo "T 检验与 Wilcoxon 检验"
echo "=========================================="
echo ""

echo "📊 相对丰度表目录：${INDIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 P 值阈值：${THRESHOLD}"
echo "📊 检验方法：${METHOD}"
echo ""

# 定义分类层级
LEVELS=("p" "c" "o" "f" "g" "s")
LEVEL_NAMES=("phylum" "class" "order" "family" "genus" "species")

# 遍历每个分类层级
for i in "${!LEVELS[@]}"; do
    level="${LEVELS[$i]}"
    level_name="${LEVEL_NAMES[$i]}"
    
    # 创建输出目录
    mkdir -p "${level_name}"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 分析 ${level_name} 水平..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Step 1: T 检验
    echo "[1/2] ${level_name}: T 检验..."
    "${PERL_BIN}" "${GET_T_WILCOX_PL}" \
        --threshold "${THRESHOLD}" \
        --infilepath "${INDIR}" \
        --group "${GROUP_FILE}" \
        --method t \
        --outdir "./${level_name}"
    
    # Step 2: Wilcoxon 检验
    echo "[2/2] ${level_name}: Wilcoxon 检验..."
    "${PERL_BIN}" "${GET_T_WILCOX_PL}" \
        --threshold "${THRESHOLD}" \
        --infilepath "${INDIR}" \
        --group "${GROUP_FILE}" \
        --method wilcox \
        --outdir "./${level_name}"
    
    echo "  ✅ ${level_name} 水平检验完成"
    echo ""
done

echo ""
echo "✅ T 检验与 Wilcoxon 检验完成"
echo ""
echo "📊 输出文件:"
echo "   - phylum/t_test_*.txt: 门水平 T 检验结果"
echo "   - phylum/wilcox_test_*.txt: 门水平 Wilcoxon 检验结果"
echo "   - class/t_test_*.txt: 纲水平 T 检验结果"
echo "   - class/wilcox_test_*.txt: 纲水平 Wilcoxon 检验结果"
echo "   - order/t_test_*.txt: 目水平 T 检验结果"
echo "   - order/wilcox_test_*.txt: 目水平 Wilcoxon 检验结果"
echo "   - family/t_test_*.txt: 科水平 T 检验结果"
echo "   - family/wilcox_test_*.txt: 科水平 Wilcoxon 检验结果"
echo "   - genus/t_test_*.txt: 属水平 T 检验结果"
echo "   - genus/wilcox_test_*.txt: 属水平 Wilcoxon 检验结果"
echo "   - species/t_test_*.txt: 种水平 T 检验结果"
echo "   - species/wilcox_test_*.txt: 种水平 Wilcoxon 检验结果"
echo ""
