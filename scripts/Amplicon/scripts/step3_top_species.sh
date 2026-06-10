#!/bin/bash
# step3_top_species.sh - Top10 物种筛选与柱状图绘制脚本
# 用法：bash step3_top_species.sh

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
GET_TABLE_HEAD2_PL="${GET_TABLE_HEAD2_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/get_table_head2.pl}"
TRAN_TAB_PL="${TRAN_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/tran_tab.pl}"
BAR_DIAGRAM_PL="${BAR_DIAGRAM_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/bar_diagram.pl}"
SVG2XXX_BIN="${SVG2XXX_BIN:-/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN GET_TABLE_HEAD2_PL TRAN_TAB_PL BAR_DIAGRAM_PL SVG2XXX_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

# 检查输入文件
if [ ! -d "Relative" ]; then
    echo "❌ 错误：Relative 目录不存在"
    echo "   请先运行 step3_table_stats.sh 生成相对丰度表"
    exit 1
fi

echo ""
echo "=========================================="
echo "Top10 物种筛选与柱状图绘制"
echo "=========================================="
echo ""

# 创建输出目录
mkdir -p top10

# 处理各分类层级
for lev in k p c o f g s; do
    echo "📊 处理 ${lev} 水平..."
    
    # 查找相对丰度文件
    sampleFile=$(ls Relative/*.${lev}.relative.xls 2>/dev/null | head -1)
    
    if [ -z "${sampleFile}" ]; then
        echo "  ⚠️  未找到 ${lev} 水平相对丰度表，跳过"
        continue
    fi
    
    echo "  输入：${sampleFile}"
    
    # Step 1: 筛选 Top10
    "${PERL_BIN}" "${GET_TABLE_HEAD2_PL}" \
        "${sampleFile}" 10 -trantab > top10/asv_table.${lev}10.relative.tran.xls
    
    # Step 2: 格式转换
    "${PERL_BIN}" "${TRAN_TAB_PL}" \
        top10/asv_table.${lev}10.relative.tran.xls \
        > top10/asv_table.${lev}10.relative.xls
    
    # Step 3: 绘制柱状图
    "${PERL_BIN}" "${BAR_DIAGRAM_PL}" \
        -table top10/asv_table.${lev}10.relative.tran.xls \
        -right -grid -rotate='-45' -x_title 'Sample Name' \
        -y_title 'Relative Abundance' -rev_sym --y_mun 0.25,4 \
        > top10/${lev}10.relative.dis.svg
    
    # Step 4: SVG → PNG 转换
    "${SVG2XXX_BIN}" top10/${lev}10.relative.dis.svg
    
    echo "  ✅ 完成：top10/asv_table.${lev}10.relative.xls, top10/${lev}10.relative.dis.png"
done

echo ""
echo "✅ Top10 物种筛选与柱状图绘制完成"
echo ""
echo "📊 输出文件:"
echo "   - top10/asv_table.*10.relative.xls: Top10 物种表"
echo "   - top10/*10.relative.dis.png: Top10 柱状图"
echo ""
