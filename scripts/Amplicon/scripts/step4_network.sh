#!/bin/bash
# step4_network.sh - 微生物网络分析脚本
# 用法：bash step4_network.sh -i <genus.relative.xls> -g <group.list> -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
DEREP_PL="${DEREP_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Network3D/derep.pl}"
GET_G_TABLE_PL="${GET_G_TABLE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/NetWork/lib/get_g_table.pl}"
NETWORK_PIPELINE_PL="${NETWORK_PIPELINE_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/NetWork/bin/network.pipelinev2.pl}"
TAB_JS_PL="${TAB_JS_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/00.Commbin/tab_js.pl}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
if [ ! -x "${PERL_BIN}" ]; then
    echo "❌ 错误：PERL_BIN 不存在：${PERL_BIN}"
    exit 1
fi
for pl in DEREP_PL GET_G_TABLE_PL NETWORK_PIPELINE_PL TAB_JS_PL; do
    if [ ! -f "${!pl}" ]; then
        echo "❌ 错误：${pl} 不存在：${!pl}"
        echo "   可通过环境变量覆盖，例如：export ${pl}=\"/your/path/to/${pl}\""
        exit 1
    fi
done

INPUT_FILE=""
GROUP_LIST=""

OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_FILE="$2"; shift 2 ;;
        -g|--group) GROUP_LIST="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step4_network.sh -i <genus.relative.xls> -g <group.list> -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -i, --input    属水平相对丰度表路径"
            echo "  -g, --group    样本分组文件（2列：样本ID \\t 组名；3列时取最后一列为组名）"
            echo "  -o, --output   输出目录"
            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
if [ -z "${INPUT_FILE}" ]; then echo "❌ 错误：必须提供 -i"; exit 1; fi
if [ -z "${GROUP_LIST}" ]; then echo "❌ 错误：必须提供 -g"; exit 1; fi
if [ ! -f "${INPUT_FILE}" ]; then echo "❌ 错误：丰度表不存在：${INPUT_FILE}"; exit 1; fi
if [ ! -f "${GROUP_LIST}" ]; then echo "❌ 错误：分组文件不存在：${GROUP_LIST}"; exit 1; fi
if [ -z "${OUTPUT_DIR}" ]; then echo "❌ 错误：必须提供 -o"; exit 1; fi

# ----- 路径转绝对路径（cd 输出目录前） -----
INPUT_FILE="$(abs_path_file "${INPUT_FILE}")"
GROUP_LIST="$(abs_path_file "${GROUP_LIST}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"
LIST_DIR="${OUTPUT_DIR}/.network_lists"
mkdir -p "${LIST_DIR}"

# 从 group.list 提取唯一组名（2 列取第 2 列，3 列及以上取最后一列）
GROUPS_FILE="${LIST_DIR}/.all_groups"
awk -F'\t' 'NF >= 2 && $1 !~ /^#/ {
    g = (NF >= 3) ? $NF : $2
    if (g != "") print g
}' "${GROUP_LIST}" | sort -u > "${GROUPS_FILE}"

if [ ! -s "${GROUPS_FILE}" ]; then
    echo "❌ 错误：分组文件中未找到有效组名"
    exit 1
fi

GROUP_SUMMARY="$(paste -sd' ' "${GROUPS_FILE}")"
GROUP_COUNT="$(wc -l < "${GROUPS_FILE}" | tr -d ' ')"

echo ""
echo "=========================================="
echo "微生物网络分析"
echo "=========================================="
echo ""

echo "📊 输入文件：${INPUT_FILE}"
echo "📊 分组文件：${GROUP_LIST}"
echo "📊 分析组数：${GROUP_COUNT}（${GROUP_SUMMARY}）"
echo ""

run_network_group() {
    local group="$1"
    local group_list_file="$2"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔬 分析 ${group} 组网络..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    cd "${OUTPUT_DIR}"
    mkdir -p "${group}"

    echo "[1/4] ${group} 组：去冗余处理..."
    "${PERL_BIN}" "${DEREP_PL}" "${INPUT_FILE}" "${group}/genus.relative.xls"

    echo "[2/4] ${group} 组：生成 OTU 表..."
    "${PERL_BIN}" "${GET_G_TABLE_PL}" "${group}/genus.relative.xls" "${group_list_file}" > "${group}/otu_table.g.relative.xls.bak"
    perl -ne 'chomp; my @ll=split/\t/;$ll[0]=~s/\.|\(|\)//g;$ll[-1]=~s/\.|\(|\)//g;print join("\t",@ll),"\n";' "${group}/otu_table.g.relative.xls.bak" > "${group}/otu_table.g.relative.xls"
    rm -f "${group}/otu_table.g.relative.xls.bak"

    echo "[3/4] ${group} 组：网络分析..."
    "${PERL_BIN}" "${NETWORK_PIPELINE_PL}" "${group}/otu_table.g.relative.xls" \
        --shdir "${group}/Shell" --outdir "${group}" --notrun
    network_sh="${group}/Shell/dot/network.dot.sh"
    if [ ! -f "${network_sh}" ]; then
        echo "❌ 错误：网络分析脚本未生成：${network_sh}"
        exit 1
    fi
    sh "${network_sh}" > "${group}/Shell/dot/network.dot.sh.o" 2> "${group}/Shell/dot/network.dot.sh.e"

    echo "[4/4] ${group} 组：生成网络交互数据..."
    if [ ! -f "${group}/dot/igraph.calculate.txt" ]; then
        echo "❌ 错误：${group} 组网络计算失败，请查看 ${group}/Shell/dot/network.dot.sh.e"
        exit 1
    fi
    cd "${group}/dot"
    "${PERL_BIN}" "${TAB_JS_PL}" igraph.calculate.txt network.js
    cd "${OUTPUT_DIR}"

    echo "  ✅ ${group} 组网络分析完成"
    echo ""
}

while IFS= read -r group || [ -n "${group}" ]; do
    [ -z "${group}" ] && continue

    group_list_file="${LIST_DIR}/${group}.list"
    awk -F'\t' -v g="${group}" '
        NF >= 2 && $1 !~ /^#/ {
            grp = (NF >= 3) ? $NF : $2
            if (grp == g) print $1 "\t" grp
        }' "${GROUP_LIST}" > "${group_list_file}"

    sample_count=$(wc -l < "${group_list_file}" | tr -d ' ')
    if [ "${sample_count}" -eq 0 ]; then
        echo "⚠️  跳过 ${group} 组：分组文件中无对应样本"
        continue
    fi

    run_network_group "${group}" "${group_list_file}"
done < "${GROUPS_FILE}"

cd "${OUTPUT_DIR}"

echo "✅ 微生物网络分析完成"
echo ""
echo "📊 输出文件（每组一个子目录）："
while IFS= read -r group || [ -n "${group}" ]; do
    [ -z "${group}" ] && continue
    if [ -d "${group}" ]; then
        echo "   - ${group}/Shell/*.sh: ${group} 组网络分析脚本"
        echo "   - ${group}/dot/igraph.calculate.txt: ${group} 组网络计算结果"
        echo "   - ${group}/dot/network.js: ${group} 组网络交互数据"
    fi
done < "${GROUPS_FILE}"
echo ""
