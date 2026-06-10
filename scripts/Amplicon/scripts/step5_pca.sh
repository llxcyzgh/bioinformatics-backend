#!/bin/bash
# step5_pca.sh - PCA 主成分分析脚本
# 用法：bash step5_pca.sh -r <asv_table.relative.xls> -g <group.list>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"

# R 脚本和 Perl 脚本路径
UOA_R_PL="${UOA_R_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/05.Diversity_analysis/lib/PCA/UOA.R}"
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

RELATIVE_TABLE=""
GROUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--relative) RELATIVE_TABLE="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step5_pca.sh -r <asv_table.relative.xls> -g <group.list>"
            echo ""
            echo "参数:"
            echo "  -r, --relative    相对丰度 ASV 表路径"
            echo "  -g, --group       样本分组文件路径"
            echo "  -h, --help        显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${RELATIVE_TABLE}" ] && { echo "❌ 错误：必须提供 -r"; exit 1; }
[ -z "${GROUP_FILE}" ] && { echo "❌ 错误：必须提供 -g"; exit 1; }
[ ! -f "${RELATIVE_TABLE}" ] && { echo "❌ 错误：相对丰度表不存在：${RELATIVE_TABLE}"; exit 1; }
[ ! -f "${GROUP_FILE}" ] && { echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; }

echo ""
echo "=========================================="
echo "PCA 主成分分析"
echo "=========================================="
echo ""

echo "📊 相对丰度表：${RELATIVE_TABLE}"
echo "📊 分组文件：${GROUP_FILE}"
echo ""

# Step 0: 调用 color_defined.pl 生成 group_col.list
echo "[0/3] 生成颜色配置文件..."
GROUP_COL_LIST="group_col.list"
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP_FILE}" "${GROUP_COL_LIST}"
echo "  ✅ 颜色配置文件已生成：${GROUP_COL_LIST}"
echo "  📝 分组数量：$(wc -l < "${GROUP_COL_LIST}")"
echo ""

# Step 1: 绘制 PCA 排序图
echo "[1/3] 绘制 PCA 排序图..."
"${RSCRIPT_BIN}" "${UOA_R_PL}" --rFile "${RELATIVE_TABLE}" --gcFile "${GROUP_COL_LIST}" --method pca --workdir .

# Step 2: PDF → PNG 转换
echo "[2/3] 转换 PDF → PNG..."
"${CONVERT_BIN}" -density 300 UOA_pca.pdf UOA_pca.png 2>/dev/null || true

# 清理临时文件
rm -f "${GROUP_COL_LIST}"

echo ""
echo "✅ PCA 主成分分析完成"
echo ""
echo "📊 输出文件:"
echo "   - UOA_pca.svg: PCA 排序图（SVG 格式）"
echo "   - UOA_pca.pdf: PCA 排序图（PDF 格式）"
echo "   - UOA_pca.png: PCA 排序图（PNG 格式）"
echo ""
