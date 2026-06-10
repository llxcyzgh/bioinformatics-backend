#!/bin/bash
# step5_pcoa.sh - PCoA 主坐标分析脚本
# 用法：bash step5_pcoa.sh -w <weighted_pc> -wu <unweighted_pc> -g <group.list>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"

# R 脚本和 Perl 脚本路径
PCOA_R_PL="${PCOA_R_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCoA/plot_PCoA.R}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in RSCRIPT_BIN CONVERT_BIN; do
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

WEIGHTED_PC=""
UNWEIGHTED_PC=""
GROUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--weighted) WEIGHTED_PC="$2"; shift 2 ;;
        -wu|--unweighted) UNWEIGHTED_PC="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step5_pcoa.sh -w <weighted_pc> -wu <unweighted_pc> -g <group.list>"
            echo ""
            echo "参数:"
            echo "  -w, --weighted    Weighted UniFrac PCoA 坐标路径"
            echo "  -wu, --unweighted Unweighted UniFrac PCoA 坐标路径"
            echo "  -g, --group       样本分组文件路径"
            echo "  -h, --help        显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${WEIGHTED_PC}" ] && { echo "❌ 错误：必须提供 -w"; exit 1; }
[ -z "${UNWEIGHTED_PC}" ] && { echo "❌ 错误：必须提供 -wu"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ ! -f "${WEIGHTED_PC}" ] && { echo "❌ 错误：Weighted PCoA 坐标不存在：${WEIGHTED_PC}"; exit 1; }
[ ! -f "${UNWEIGHTED_PC}" ] && { echo "❌ 错误：Unweighted PCoA 坐标不存在：${UNWEIGHTED_PC}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

echo ""
echo "=========================================="
echo "PCoA 主坐标分析"
echo "=========================================="
echo ""

echo "📊 Weighted UniFrac PCoA 坐标：${WEIGHTED_PC}"
echo "📊 Unweighted UniFrac PCoA 坐标：${UNWEIGHTED_PC}"
echo "📊 分组文件：${GROUP_FILE}"
echo ""

# Step 0: 调用 color_defined.pl 生成 group_col.list
echo "[0/3] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

# 创建输出目录
mkdir -p PCoA/{weighted_unifrac,unweighted_unifrac}

# Step 1: 绘制 Weighted UniFrac PCoA 图
echo "[1/3] 绘制 Weighted UniFrac PCoA 图..."
cd PCoA/weighted_unifrac
"${RSCRIPT_BIN}" "${PCOA_R_PL}" --unifrac_pc "${WEIGHTED_PC}" --group_col "${GROUP_COL_LIST}" --outdir .
cd ../..

# Step 2: 绘制 Unweighted UniFrac PCoA 图
echo "[2/3] 绘制 Unweighted UniFrac PCoA 图..."
cd PCoA/unweighted_unifrac
"${RSCRIPT_BIN}" "${PCOA_R_PL}" --unifrac_pc "${UNWEIGHTED_PC}" --group_col "${GROUP_COL_LIST}" --outdir .
cd ..

# Step 3: 合并 PCoA 图
echo "[3/3] 合并 PCoA 图..."
"${CONVERT_BIN}" +append PCoA/weighted_unifrac/PCoA12.pdf PCoA/unweighted_unifrac/PCoA12.pdf PCoA/PCoA.pdf
"${CONVERT_BIN}" +append PCoA/weighted_unifrac/PCoA12.png PCoA/unweighted_unifrac/PCoA12.png PCoA/PCoA.png

# 清理临时文件
rm -f "${GROUP_COL_LIST}"

echo ""
echo "✅ PCoA 主坐标分析完成"
echo ""
echo "📊 输出目录：PCoA/"
echo "📊 关键文件:"
echo "   - PCoA/PCoA.pdf: PCoA 合并排序图（PDF 格式）"
echo "   - PCoA/PCoA.png: PCoA 合并排序图（PNG 格式）"
echo "   - PCoA/weighted_unifrac/PCoA12.pdf: Weighted UniFrac PCoA 图"
echo "   - PCoA/unweighted_unifrac/PCoA12.png: Unweighted UniFrac PCoA 图"
echo ""
