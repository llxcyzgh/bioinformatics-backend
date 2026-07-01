#!/bin/bash
# step0_pre_color.sh - 分组颜色配置文件生成脚本
# 用法：bash step0_pre_color.sh -i <group> -o <output>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
COLOR_DEFINED_PL="${COLOR_DEFINED_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/color_defined.pl}"

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

for bin in PERL_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        exit 1
    fi
done
if [ ! -f "${COLOR_DEFINED_PL}" ]; then
    echo "❌ 错误：color_defined.pl 不存在：${COLOR_DEFINED_PL}"
    exit 1
fi

GROUP=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--group) GROUP="$2"; shift 2 ;;
        -o|--output) OUTPUT="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step0_pre_color.sh -i <group> -o <output>"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

[ -z "${GROUP}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${OUTPUT}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# ----- 输入路径转绝对路径 -----
GROUP="$(abs_path_file "${GROUP}")"
OUTPUT="$(abs_path_out_file "${OUTPUT}")"
# ---------------------------------

echo ""
echo "=========================================="
echo "分组颜色配置文件生成"
echo "=========================================="
echo ""

echo "🎨 执行 color_defined.pl..."
"${PERL_BIN}" "${COLOR_DEFINED_PL}" "${GROUP}" "${OUTPUT}"

echo "✅ 分组颜色配置文件生成完成"
echo ""
echo "📁 输入：${GROUP}"
echo "📁 输出：${OUTPUT}"
echo "📊 文件格式：三列 TSV (样本 ID、分组名、颜色代码)"
echo ""
