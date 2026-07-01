#!/bin/bash
# step3_top_species.sh - Top10 物种筛选与柱状图绘制脚本
# 用法：bash step3_top_species.sh -i <Relative/> -o <output_dir> [-g <group.list>]

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

RELATIVE_DIR=""
GROUP_LIST=""
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) RELATIVE_DIR="$2"; shift 2 ;;
        -g|--group) GROUP_LIST="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step3_top_species.sh -i <Relative/> -o <output_dir> [-g <group.list>]"
            echo ""
            echo "参数:"
            echo "  -i, --input      相对丰度表目录路径（含 *.relative.xls）"
            echo "  -g, --group      样本分组文件（可选，用于计算分组 Top10）"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${RELATIVE_DIR}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }
[ ! -d "${RELATIVE_DIR}" ] && { echo "❌ 错误：Relative 目录不存在：${RELATIVE_DIR}"; exit 1; }
if [ -n "${GROUP_LIST}" ] && [ ! -f "${GROUP_LIST}" ]; then
    echo "❌ 错误：分组文件不存在：${GROUP_LIST}"
    exit 1
fi

# ----- 路径转绝对路径（cd 输出目录前） -----
RELATIVE_DIR="$(abs_path_dir "${RELATIVE_DIR}")"
GROUP_LIST="$(abs_path_file_optional "${GROUP_LIST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
GET_TABLE_HEAD2_PL="${GET_TABLE_HEAD2_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/get_table_head2.pl}"
TRAN_TAB_PL="${TRAN_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/tran_tab.pl}"
BAR_DIAGRAM_PL="${BAR_DIAGRAM_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/bar_diagram.pl}"
COMBINE_TABLE_PL="${COMBINE_TABLE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/test_bin/Combine_table.pl}"
SVG2XXX_BIN="${SVG2XXX_BIN:-/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN SVG2XXX_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done
for script in GET_TABLE_HEAD2_PL TRAN_TAB_PL BAR_DIAGRAM_PL; do
    if [ ! -f "${!script}" ]; then
        echo "❌ 错误：${script} 不存在：${!script}"
        exit 1
    fi
done
if [ -n "${GROUP_LIST}" ] && [ ! -f "${COMBINE_TABLE_PL}" ]; then
    echo "❌ 错误：COMBINE_TABLE_PL 不存在：${COMBINE_TABLE_PL}"
    exit 1
fi

echo ""
echo "=========================================="
echo "Top10 物种筛选与柱状图绘制"
echo "=========================================="
echo ""
echo "📊 输入目录：${RELATIVE_DIR}"
mkdir -p top10
if [ -n "${GROUP_LIST}" ]; then
    echo "📊 分组文件：${GROUP_LIST}"
    mkdir -p top10_group
fi
echo ""
# 处理各分类层级
for lev in k p c o f g s; do
    echo "📊 处理 ${lev} 水平..."
    
    # 查找相对丰度文件
    sampleFile=$(ls ${RELATIVE_DIR}/*.${lev}.relative.xls 2>/dev/null | head -1)
    
    if [ -z "${sampleFile}" ]; then
        echo "  ⚠️  未找到 ${lev} 水平相对丰度表，跳过"
        continue
    fi
    
    echo "  输入：${sampleFile}"
    
    # Step 1: 筛选 Top10
    "${PERL_BIN}" "${GET_TABLE_HEAD2_PL}" \
        "${sampleFile}" 10 -trantab > "top10/asv_table.${lev}10.relative.tran.xls"
    
    # Step 2: 格式转换
    "${PERL_BIN}" "${TRAN_TAB_PL}" \
        "top10/asv_table.${lev}10.relative.tran.xls" \
        > "top10/asv_table.${lev}10.relative.xls"
    
    # Step 3: 绘制柱状图
    "${PERL_BIN}" "${BAR_DIAGRAM_PL}" \
        -table "top10/asv_table.${lev}10.relative.tran.xls" \
        -right -grid -rotate='-45' -x_title 'Sample Name' \
        -y_title 'Relative Abundance' -rev_sym --y_mun 0.25,4 \
        > "top10/${lev}10.relative.dis.svg"
    
    # Step 4: SVG → PNG 转换
    "${SVG2XXX_BIN}" "top10/${lev}10.relative.dis.svg"
    
    echo "  ✅ 样本 Top10：top10/asv_table.${lev}10.relative.xls, top10/${lev}10.relative.dis.png"

    # 分组 Top10（可选）
    if [ -n "${GROUP_LIST}" ]; then
        echo "  📊 分组 Top10 (${lev})..."
        "${PERL_BIN}" "${COMBINE_TABLE_PL}" \
            "top10/asv_table.${lev}10.relative.xls" \
            "${GROUP_LIST}" \
            > "top10_group/asv_table.${lev}10.group.relative.xls"

        "${PERL_BIN}" "${TRAN_TAB_PL}" \
            "top10_group/asv_table.${lev}10.group.relative.xls" \
            > "top10_group/asv_table.${lev}10.group.relative.tran.xls"

        "${PERL_BIN}" "${BAR_DIAGRAM_PL}" \
            -table "top10_group/asv_table.${lev}10.group.relative.tran.xls" \
            -right -grid -rotate='-45' -x_title 'Group Name' \
            -y_title 'Relative Abundance' -rev_sym --y_mun 0.25,4 \
            > "top10_group/${lev}10.group.relative.dis.svg"

        "${SVG2XXX_BIN}" "top10_group/${lev}10.group.relative.dis.svg"

        echo "  ✅ 分组 Top10：top10_group/asv_table.${lev}10.group.relative.xls, top10_group/${lev}10.group.relative.dis.png"
    fi
done

echo ""
echo "✅ Top10 物种筛选与柱状图绘制完成"
echo ""
echo "📊 输出文件:"
echo "   - top10/asv_table.*10.relative.xls: 样本 Top10 物种表"
echo "   - top10/*10.relative.dis.png: 样本 Top10 柱状图"
if [ -n "${GROUP_LIST}" ]; then
    echo "   - top10_group/asv_table.*10.group.relative.xls: 分组 Top10 物种表"
    echo "   - top10_group/*10.group.relative.dis.png: 分组 Top10 柱状图"
fi
echo ""
