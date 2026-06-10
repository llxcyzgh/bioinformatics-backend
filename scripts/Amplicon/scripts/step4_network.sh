#!/bin/bash
# step4_network.sh - 微生物网络分析脚本
# 用法：bash step4_network.sh -i <genus.relative.xls> -y <Y.list> -z <Z.list>

set -e

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
for bin in PERL_BIN DEREP_PL GET_G_TABLE_PL NETWORK_PIPELINE_PL TAB_JS_PL; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INPUT_FILE=""
Y_LIST=""
Z_LIST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_FILE="$2"; shift 2 ;;
        -y|--y-list) Y_LIST="$2"; shift 2 ;;
        -z|--z-list) Z_LIST="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_network.sh -i <genus.relative.xls> -y <Y.list> -z <Z.list>"
            echo ""
            echo "参数:"
            echo "  -i, --input    属水平相对丰度表路径"
            echo "  -y, --y-list   Y 组样本列表路径"
            echo "  -z, --z-list   Z 组样本列表路径"
            echo "  -h, --help     显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INPUT_FILE}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ -z "${Y_LIST}" ] && { echo "❌ 错误：必须提供 -y"; exit 1; }
[ -z "${Z_LIST}" ] && { echo "❌ 错误：必须提供 -z"; exit 1; }
[ ! -f "${INPUT_FILE}" ] && { echo "❌ 错误：丰度表不存在：${INPUT_FILE}"; exit 1; }
[ ! -f "${Y_LIST}" ] && { echo "❌ 错误：Y 组列表不存在：${Y_LIST}"; exit 1; }
[ ! -f "${Z_LIST}" ] && { echo "❌ 错误：Z 组列表不存在：${Z_LIST}"; exit 1; }

echo ""
echo "=========================================="
echo "微生物网络分析"
echo "=========================================="
echo ""

echo "📊 输入文件：${INPUT_FILE}"
echo "📊 Y 组列表：${Y_LIST}"
echo "📊 Z 组列表：${Z_LIST}"
echo ""

# 处理 Y 组
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔬 分析 Y 组网络..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p Y

# Step 1: 去冗余处理
echo "[1/4] Y 组：去冗余处理..."
"${PERL_BIN}" "${DEREP_PL}" "${INPUT_FILE}" Y/genus.relative.xls

# Step 2: 生成 OTU 表
echo "[2/4] Y 组：生成 OTU 表..."
"${PERL_BIN}" "${GET_G_TABLE_PL}" Y/genus.relative.xls "${Y_LIST}" > Y/otu_table.g.relative.xls.bak
perl -ne 'chomp; my @ll=split/\t/;$ll[0]=~s/\.|\(|\)//g;$ll[-1]=~s/\.|\(|\)//g;print join("\t",@ll),"\n";' Y/otu_table.g.relative.xls.bak > Y/otu_table.g.relative.xls
rm -f Y/otu_table.g.relative.xls.bak

# Step 3: 网络分析
echo "[3/4] Y 组：网络分析..."
"${PERL_BIN}" "${NETWORK_PIPELINE_PL}" Y/otu_table.g.relative.xls --shdir Y/Shell --outdir Y

# Step 4: 生成网络交互数据
echo "[4/4] Y 组：生成网络交互数据..."
cd Y/dot
"${PERL_BIN}" "${TAB_JS_PL}" igraph.calculate.txt network.js
cd ..

echo "  ✅ Y 组网络分析完成"
echo ""

# 处理 Z 组
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔬 分析 Z 组网络..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p Z

# Step 1: 去冗余处理
echo "[1/4] Z 组：去冗余处理..."
"${PERL_BIN}" "${DEREP_PL}" "${INPUT_FILE}" Z/genus.relative.xls

# Step 2: 生成 OTU 表
echo "[2/4] Z 组：生成 OTU 表..."
"${PERL_BIN}" "${GET_G_TABLE_PL}" Z/genus.relative.xls "${Z_LIST}" > Z/otu_table.g.relative.xls.bak
perl -ne 'chomp; my @ll=split/\t/;$ll[0]=~s/\.|\(|\)//g;$ll[-1]=~s/\.|\(|\)//g;print join("\t",@ll),"\n";' Z/otu_table.g.relative.xls.bak > Z/otu_table.g.relative.xls
rm -f Z/otu_table.g.relative.xls.bak

# Step 3: 网络分析
echo "[3/4] Z 组：网络分析..."
"${PERL_BIN}" "${NETWORK_PIPELINE_PL}" Z/otu_table.g.relative.xls --shdir Z/Shell --outdir Z

# Step 4: 生成网络交互数据
echo "[4/4] Z 组：生成网络交互数据..."
cd Z/dot
"${PERL_BIN}" "${TAB_JS_PL}" igraph.calculate.txt network.js
cd ..

echo "  ✅ Z 组网络分析完成"
echo ""

echo "✅ 微生物网络分析完成"
echo ""
echo "📊 输出文件:"
echo "   - Y/Shell/*.sh: Y 组网络分析脚本"
echo "   - Y/dot/igraph.calculate.txt: Y 组网络计算结果"
echo "   - Y/dot/network.js: Y 组网络交互数据"
echo "   - Z/Shell/*.sh: Z 组网络分析脚本"
echo "   - Z/dot/igraph.calculate.txt: Z 组网络计算结果"
echo "   - Z/dot/network.js: Z 组网络交互数据"
echo ""
