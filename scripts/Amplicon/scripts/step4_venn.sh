#!/bin/bash
# step4_venn.sh - 维恩图分析脚本
# 用法：bash step4_venn.sh -t <asv_table.group.even.txt|asv_table.even.txt> [-g <group.list>] -l <venn_list> -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
COMBINE_SAMPLE2GROUP_PL="${COMBINE_SAMPLE2GROUP_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/combineTableFromSample2Group.pl}"
VENN_PL="${VENN_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/venn.pl}"

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -x "${PERL_BIN}" ]; then
    echo "❌ 错误：PERL_BIN 不存在：${PERL_BIN}"
    exit 1
fi
if [ ! -f "${VENN_PL}" ]; then
    echo "❌ 错误：venn.pl 不存在：${VENN_PL}"
    exit 1
fi

TABLE_FILE=""
GROUP_FILE=""
VENN_LIST=""
OUTPUT_DIR=""
GENERATED_GROUP_TABLE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--table) TABLE_FILE="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -l|--list) VENN_LIST="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_venn.sh -t <table> [-g <group.list>] -l <list> -o <output>"
            echo ""
            echo "参数:"
            echo "  -t, --table      分组 ASV 表（asv_table.group.even.txt），"
            echo "                   或样本均一化表（asv_table.even.txt，需配合 -g）"
            echo "  -g, --group      样本分组文件（-t 为 asv_table.even.txt 时必需）"
            echo "  -l, --list       维恩图分组列表"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${TABLE_FILE}" ] && { echo "❌ 错误：必须提供 -t"; exit 1; }
[ -z "${VENN_LIST}" ] && { echo "❌ 错误：必须提供 -l"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
[ ! -f "${TABLE_FILE}" ] && { echo "❌ 错误：ASV 表不存在：${TABLE_FILE}"; exit 1; }
[ ! -f "${VENN_LIST}" ] && { echo "❌ 错误：维恩图列表不存在：${VENN_LIST}"; exit 1; }

table_base="$(basename "${TABLE_FILE}")"
if [ -n "${GROUP_FILE}" ]; then
    [ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }
    if [ ! -f "${COMBINE_SAMPLE2GROUP_PL}" ]; then
        echo "❌ 错误：COMBINE_SAMPLE2GROUP_PL 不存在：${COMBINE_SAMPLE2GROUP_PL}"
        exit 1
    fi
elif [ "${table_base}" = "asv_table.even.txt" ]; then
    echo "❌ 错误：-t 为 asv_table.even.txt 时必须提供 -g group.list"
    exit 1
fi

# ----- 路径转绝对路径（cd 输出目录前） -----
TABLE_FILE="$(abs_path_file "${TABLE_FILE}")"
GROUP_FILE="$(abs_path_file_optional "${GROUP_FILE}")"
VENN_LIST="$(abs_path_file "${VENN_LIST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "维恩图分析"
echo "=========================================="
echo ""

if [ -n "${GROUP_FILE}" ]; then
    echo "📊 样本均一化 ASV 表：${TABLE_FILE}"
    echo "📊 分组文件：${GROUP_FILE}"
    echo "[0/N] 生成分组均一化 ASV 表..."
    "${PERL_BIN}" "${COMBINE_SAMPLE2GROUP_PL}" \
        "${TABLE_FILE}" \
        "${GROUP_FILE}" \
        > asv_table.group.even.txt
    echo "  ✅ 已生成 asv_table.group.even.txt"
    VENN_TABLE="asv_table.group.even.txt"
    GENERATED_GROUP_TABLE=1
else
    VENN_TABLE="${TABLE_FILE}"
    echo "📊 分组 ASV 表：${VENN_TABLE}"
fi

echo "📊 维恩图列表：${VENN_LIST}"
echo ""

echo "🎨 绘制维恩图..."
"${PERL_BIN}" "${VENN_PL}" \
    "${VENN_TABLE}" "${VENN_LIST}" > Venn_group.log

echo "✅ 维恩图绘制完成"
echo ""
echo "📁 输出目录：${OUTPUT_DIR}"
echo "📊 关键文件:"
echo "   - *.svg/png: 维恩图图片"
echo "   - *.xls: 维恩图数据表"
if [ "${GENERATED_GROUP_TABLE}" -eq 1 ]; then
    echo "   - asv_table.group.even.txt: 由 group.list 汇总的分组均一化 ASV 表"
fi
echo ""
