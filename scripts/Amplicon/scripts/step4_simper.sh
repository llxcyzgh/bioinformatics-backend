#!/bin/bash
# step4_simper.sh - SIMPER 相似性百分比分析脚本
# 用法：bash step4_simper.sh -i <Relative/> -g <group.list> [--top <N>]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
GET_SIMPER_PL="${GET_SIMPER_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/simper/get.simper.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN GET_SIMPER_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INDIR=""
GROUP_FILE=""
TOP_N="10"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INDIR="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        --top) TOP_N="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_simper.sh -i <Relative/> -g <group.list> [--top <N>]"
            echo ""
            echo "参数:"
            echo "  -i, --input    相对丰度表目录路径"
            echo "  -g, --group    样本分组文件路径"
            echo "  --top          Top 物种数量（默认：10）"
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
echo "SIMPER 相似性百分比分析"
echo "=========================================="
echo ""

echo "📊 相对丰度表目录：${INDIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 Top 物种数量：${TOP_N}"
echo ""

# 执行 SIMPER 分析
echo "[1/1] 执行 SIMPER 分析..."
"${PERL_BIN}" "${GET_SIMPER_PL}" \
    --infilepath "${INDIR}" \
    --group "${GROUP_FILE}" \
    --top "${TOP_N}" \
    --outdir ./

echo ""
echo "✅ SIMPER 分析完成"
echo ""
echo "📊 输出文件:"
echo "   - phylum/simper_*.txt: 门水平 SIMPER 结果"
echo "   - class/simper_*.txt: 纲水平 SIMPER 结果"
echo "   - order/simper_*.txt: 目水平 SIMPER 结果"
echo "   - family/simper_*.txt: 科水平 SIMPER 结果"
echo "   - genus/simper_*.txt: 属水平 SIMPER 结果"
echo "   - species/simper_*.txt: 种水平 SIMPER 结果"
echo ""
