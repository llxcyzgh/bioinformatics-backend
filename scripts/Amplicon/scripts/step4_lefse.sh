#!/bin/bash
# step4_lefse.sh - LEfSe 线性判别分析效应大小脚本
# 用法：bash step4_lefse.sh -i <Relative/> -m <all.mf> -v <lefse_vs.list>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
PLOT_LEFSE_PL="${PLOT_LEFSE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/plot_lefse.pl}"
SVG2XXX_BIN="${SVG2XXX_BIN:-/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/svg2xxx_release/svg2xxx}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN PLOT_LEFSE_PL SVG2XXX_BIN CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

RELATIVE_DIR=""
META_FILE=""
VS_LIST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) RELATIVE_DIR="$2"; shift 2 ;;
        -m|--meta) META_FILE="$2"; shift 2 ;;
        -v|--vs-list) VS_LIST="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_lefse.sh -i <Relative/> -m <all.mf> -v <lefse_vs.list>"
            echo ""
            echo "参数:"
            echo "  -i, --input      相对丰度表目录路径"
            echo "  -m, --meta       样本元数据文件路径"
            echo "  -v, --vs-list    LEfSe 对比分组列表路径"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${RELATIVE_DIR}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${META_FILE}" ] && { echo "❌ 错误：必须提供 -m"; exit 1; }
[ -z "${VS_LIST}" ] && { echo "❌ 错误：必须提供 -v"; exit 1; }
[ ! -d "${RELATIVE_DIR}" ] && { echo "❌ 错误：相对丰度表目录不存在：${RELATIVE_DIR}"; exit 1; }
[ ! -f "${META_FILE}" ] && { echo "❌ 错误：元数据文件不存在：${META_FILE}"; exit 1; }
[ ! -f "${VS_LIST}" ] && { echo "❌ 错误：对比分组列表不存在：${VS_LIST}"; exit 1; }

echo ""
echo "=========================================="
echo "LEfSe 线性判别分析效应大小"
echo "=========================================="
echo ""

echo "📊 相对丰度表目录：${RELATIVE_DIR}"
echo "📊 样本元数据：${META_FILE}"
echo "📊 对比分组列表：${VS_LIST}"
echo ""

# Step 1: 执行 plot_lefse.pl
echo "[1/5] 执行 LEfSe 分析..."
"${PERL_BIN}" "${PLOT_LEFSE_PL}" \
    "${RELATIVE_DIR}" \
    "${META_FILE}" \
    --lefse_vs "${VS_LIST}" \
    --list_options='--format svg' \
    --tree_options='--format svg --right_space_prop 0.15'

# Step 2: SVG → PDF 转换
echo "[2/5] 转换 SVG → PDF..."
"${PERL_BIN}" -e 'for (`ls */*.svg`){chomp; if (-s $_){/(.*).svg/; system"'"${SVG2XXX_BIN}"' $1.svg -t pdf";}}'

# Step 3: 复制最佳结果到当前目录
echo "[3/5] 复制最佳结果..."
"${PERL_BIN}" -e 'chomp(@list = `ls`);for my $dir(@list){if($dir=~/^(\d+)/){$sign=$1;}if(-s "$dir/LDA.$sign.png"){`cp -f $dir/LDA.$sign.png LDA.png;cp -f $dir/LDA.$sign.pdf LDA.pdf;cp -f $dir/LDA.$sign.tree.png LDA.tree.png;cp -f $dir/LDA.$sign.tree.pdf LDA.tree.pdf`;last;}}'

# Step 4: 合并图片
echo "[4/5] 合并 LDA 图和进化树..."
"${CONVERT_BIN}" +append LDA.pdf LDA.tree.pdf LEfSe.pdf
"${CONVERT_BIN}" +append LDA.png LDA.tree.png LEfSe.png

echo ""
echo "✅ LEfSe 分析完成"
echo ""
echo "📊 输出文件:"
echo "   - LEfSe.png: LDA 判别图 + 进化树合并图（PNG）"
echo "   - LEfSe.pdf: LDA 判别图 + 进化树合并图（PDF）"
echo "   - LDA.png: LDA 判别分析图（PNG）"
echo "   - LDA.pdf: LDA 判别分析图（PDF）"
echo "   - LDA.tree.png: 进化树分支图（PNG）"
echo "   - LDA.tree.pdf: 进化树分支图（PDF）"
echo ""
