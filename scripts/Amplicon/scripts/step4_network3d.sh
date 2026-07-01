#!/bin/bash
# step4_network3d.sh - 3D 微生物网络可视化脚本
# 用法：bash step4_network3d.sh -i <genus.relative.xls> [-n <top_n>] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
DEREP_PL="${DEREP_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/derep.pl}"
MAP_PL="${MAP_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/map.pl}"
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
NET_FILE_GENERATE_R="${NET_FILE_GENERATE_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/net_file_generate.R}"
BAYES_NET_PLOT_R="${BAYES_NET_PLOT_R:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/Bayes_net_plot.R}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN DEREP_PL MAP_PL RSCRIPT_BIN NET_FILE_GENERATE_R BAYES_NET_PLOT_R; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INPUT_FILE=""
TOP_N="100"

OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_FILE="$2"; shift 2 ;;
        -n|--top-n) TOP_N="$2"; shift 2 ;;
                -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step4_network3d.sh -i <genus.relative.xls> [-n <top_n>]"
            echo ""
            echo "参数:"
            echo "  -i, --input    属水平相对丰度表路径"
            echo "  -n, --top-n    Top 物种数量（默认：100）"
            echo "  -o, --output     输出目录"

            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INPUT_FILE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ ! -f "${INPUT_FILE}" ] && { echo "❌ 错误：丰度表不存在：${INPUT_FILE}"; exit 1; }

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# ----- 路径转绝对路径（cd 输出目录前） -----
INPUT_FILE="$(abs_path_file "${INPUT_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

echo ""
echo "=========================================="
echo "3D 微生物网络可视化"
echo "=========================================="
echo ""

echo "📊 输入文件：${INPUT_FILE}"
echo "📊 Top 物种数量：${TOP_N}"
echo ""

# Step 1: 去冗余处理
echo "[1/4] 去冗余处理..."
"${PERL_BIN}" "${DEREP_PL}" "${INPUT_FILE}" genus.relative.txt

# Step 2: 生成物种映射
echo "[2/4] 生成物种映射..."
"${PERL_BIN}" "${MAP_PL}" genus.relative.txt > map.txt

# Step 3: 生成网络文件
echo "[3/4] 生成网络文件..."
"${RSCRIPT_BIN}" "${NET_FILE_GENERATE_R}" \
    -i genus.relative.txt \
    -f map.txt \
    -n "${TOP_N}" \
    -o ./

# Step 4: 绘制 3D 网络
echo "[4/4] 绘制 3D 网络..."
"${RSCRIPT_BIN}" "${BAYES_NET_PLOT_R}" \
    -e edgeplot.xls \
    -d node.xls \
    -o ./

echo ""
echo "✅ 3D 微生物网络可视化完成"
echo ""
echo "📊 输出文件:"
echo "   - map.txt: 物种映射文件"
echo "   - edgeplot.xls: 边数据文件"
echo "   - node.xls: 节点数据文件"
if [ -f "network3D.html" ]; then
    echo "   - network3D.html: 3D 网络可视化（用浏览器打开）"
fi
echo ""
echo "💡 使用方法：用浏览器打开 network3D.html 查看 3D 交互式网络"
echo ""
