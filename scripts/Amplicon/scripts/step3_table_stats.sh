#!/bin/bash
# step3_table_stats.sh - ASV 表均一化与相对丰度脚本
# 用法：bash step3_table_stats.sh -i <asv_table.txt> -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"
COMBINE_TABLE_PL="${COMBINE_TABLE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/Combine_table.pl}"
COMBINE_SAMPLE2GROUP_PL="${COMBINE_SAMPLE2GROUP_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/combineTableFromSample2Group.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在（perl 脚本用 -f，可执行程序用 -x）
for bin in PERL_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done
if [ ! -f "${STAT_OTU_TAB_PL}" ]; then
    echo "❌ 错误：STAT_OTU_TAB_PL 不存在：${STAT_OTU_TAB_PL}"
    echo "   可通过环境变量覆盖，例如：export STAT_OTU_TAB_PL=\"/your/path/to/stat_otu_tab.pl\""
    exit 1
fi

ASV_TABLE=""
GROUP_LIST=""
OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) ASV_TABLE="$2"; shift 2 ;;
        -g|--group) GROUP_LIST="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step3_table_stats.sh -i <asv_table.txt> -o <output_dir> [-g <group.list>]"
            echo ""
            echo "参数:"
            echo "  -i, --input      ASV 表文件路径"
            echo "  -g, --group      样本分组文件（可选，用于计算分组均一化表与分组相对丰度）"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${ASV_TABLE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ ! -f "${ASV_TABLE}" ] && { echo "❌ 错误：ASV 表不存在：${ASV_TABLE}"; exit 1; }

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
if [ -n "${GROUP_LIST}" ] && [ ! -f "${GROUP_LIST}" ]; then
    echo "❌ 错误：分组文件不存在：${GROUP_LIST}"
    exit 1
fi
if [ -n "${GROUP_LIST}" ] && [ ! -f "${COMBINE_TABLE_PL}" ]; then
    echo "❌ 错误：COMBINE_TABLE_PL 不存在：${COMBINE_TABLE_PL}"
    exit 1
fi
if [ -n "${GROUP_LIST}" ] && [ ! -f "${COMBINE_SAMPLE2GROUP_PL}" ]; then
    echo "❌ 错误：COMBINE_SAMPLE2GROUP_PL 不存在：${COMBINE_SAMPLE2GROUP_PL}"
    exit 1
fi

# ----- 路径转绝对路径（cd 输出目录前） -----
ASV_TABLE="$(abs_path_file "${ASV_TABLE}")"
GROUP_LIST="$(abs_path_file_optional "${GROUP_LIST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "ASV 表均一化与相对丰度"
echo "=========================================="
echo ""

echo "📊 输入文件：${ASV_TABLE}"
if [ -n "${GROUP_LIST}" ]; then
    echo "📊 分组文件：${GROUP_LIST}"
fi
echo ""

TOTAL_STEPS=2
[ -n "${GROUP_LIST}" ] && TOTAL_STEPS=4

# Step 1: 数据均一化
echo "[1/${TOTAL_STEPS}] 数据均一化..."
"${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
    "${ASV_TABLE}" \
    --even asv_table.even.txt \
    -unif min

# Step 2: 计算相对丰度
echo "[2/${TOTAL_STEPS}] 计算样本相对丰度..."
mkdir -p Relative
"${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
    asv_table.even.txt \
    --prefix Relative/asv_table

# Step 3-4: 分组均一化表与分组相对丰度（可选）
if [ -n "${GROUP_LIST}" ]; then
    echo "[3/${TOTAL_STEPS}] 计算分组均一化表..."
    "${PERL_BIN}" "${COMBINE_SAMPLE2GROUP_PL}" \
        asv_table.even.txt \
        "${GROUP_LIST}" \
        > asv_table.group.even.txt
    echo "   ✅ 已生成 asv_table.group.even.txt"

    echo "[4/${TOTAL_STEPS}] 计算分组相对丰度..."
    mkdir -p Relative_group
    for lev in k p c o f g s; do
        echo "  ${lev} 水平..."
        "${PERL_BIN}" "${COMBINE_TABLE_PL}" \
            "Relative/asv_table.${lev}.relative.xls" \
            "${GROUP_LIST}" \
            > "Relative_group/asv_table_group.${lev}.relative.xls"
    done
fi

echo ""
echo "✅ ASV 表均一化与相对丰度计算完成"
echo ""
echo "📊 输出文件:"
echo "   - asv_table.even.txt: 均一化 ASV 表"
echo "   - Relative/: 各层级样本相对丰度表 (k/p/c/o/f/g/s)"
if [ -n "${GROUP_LIST}" ]; then
    echo "   - asv_table.group.even.txt: 分组均一化 ASV 表"
    echo "   - Relative_group/: 各层级分组相对丰度表 (k/p/c/o/f/g/s)"
fi
echo ""
