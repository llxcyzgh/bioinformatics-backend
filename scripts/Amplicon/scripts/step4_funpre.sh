#!/bin/bash
# step4_funpre.sh - PICRUSt2 功能预测分析脚本
# 用法：bash step4_funpre.sh -b <featureTable.biom|featureTable.tsv> -s <feature.fasta> [-g <group.list>] [-v <venng.list>]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
PICRUSt2_PL="${PICRUSt2_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/Funnction_prediction/PICRUSt2/PICRUSt2.pl}"
BIOM_BIN="${BIOM_BIN:-/software/anaconda3/envs/16s-env/bin/biom}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in PERL_BIN PICRUSt2_PL BIOM_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INPUT_TABLE=""
REP_SEQS=""
GROUP_LIST=""
VENNG_LIST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--biom) INPUT_TABLE="$2"; shift 2 ;;
        -s|--seqs) REP_SEQS="$2"; shift 2 ;;
        -g|--group) GROUP_LIST="$2"; shift 2 ;;
        -v|--venn) VENNG_LIST="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step4_funpre.sh -b <featureTable.biom|featureTable.tsv> -s <feature.fasta> [-g <group.list>] [-v <venng.list>]"
            echo ""
            echo "参数:"
            echo "  -b, --biom     ASV 丰度表（BIOM 或 TSV 格式）"
            echo "  -s, --seqs     ASV 代表序列（FASTA）"
            echo "  -g, --group    样本分组文件路径（可选）"
            echo "  -v, --venn     功能维恩图分组列表路径（可选）"
            echo "  -h, --help     显示帮助"
            echo ""
            echo "说明:"
            echo "  如果输入是 TSV 格式，脚本会自动转换为 BIOM 格式"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INPUT_TABLE}" ] && { echo "❌ 错误：必须提供 -b"; exit 1; }
[ -z "${REP_SEQS}" ] && { echo "❌ 错误：必须提供 -s"; exit 1; }
[ ! -f "${INPUT_TABLE}" ] && { echo "❌ 错误：输入文件不存在：${INPUT_TABLE}"; exit 1; }
[ ! -f "${REP_SEQS}" ] && { echo "❌ 错误：序列文件不存在：${REP_SEQS}"; exit 1; }

echo ""
echo "=========================================="
echo "PICRUSt2 功能预测分析"
echo "=========================================="
echo ""

# Step 0: 检查输入格式并转换（如果是 TSV）
BIOM_TABLE="${INPUT_TABLE}"
if [[ "${INPUT_TABLE}" == *.tsv || "${INPUT_TABLE}" == *.txt ]]; then
    echo "[0/6] 检测输入格式：TSV"
    echo "🔄 转换 TSV → BIOM..."
    BIOM_TABLE="featureTable.biom"
    
    # 使用 biom convert 转换
    "${BIOM_BIN}" convert \
        -i "${INPUT_TABLE}" \
        -o "${BIOM_TABLE}" \
        --to-json \
        --table-type="OTU table"
    
    echo "  ✅ BIOM 文件已生成：${BIOM_TABLE}"
elif [[ "${INPUT_TABLE}" == *.biom ]]; then
    echo "[0/6] 检测输入格式：BIOM"
    echo "  ✅ 无需转换"
else
    echo "⚠️  未知文件格式：${INPUT_TABLE}"
    echo "   支持的格式：.biom, .tsv, .txt"
    exit 1
fi

echo "📊 输入文件：${BIOM_TABLE}"
echo "📊 代表序列：${REP_SEQS}"
if [ -n "${GROUP_LIST}" ] && [ -f "${GROUP_LIST}" ]; then
    echo "📊 分组文件：${GROUP_LIST}"
fi
if [ -n "${VENNG_LIST}" ] && [ -f "${VENNG_LIST}" ]; then
    echo "📊 功能维恩图分组：${VENNG_LIST}"
fi
echo ""

# Step 1: 构建 PICRUSt2.pl 命令参数
PICRUSt_ARGS="--otu_biom ${BIOM_TABLE} --rep_seq ${REP_SEQS}"

# 添加可选参数
if [ -n "${GROUP_LIST}" ] && [ -f "${GROUP_LIST}" ]; then
    PICRUSt_ARGS="${PICRUSt_ARGS} --grouplist ${GROUP_LIST}"
    # 自动生成 group_col.list（如果存在 group.list）
    GROUP_COL_LIST="group_col.list"
    if [ -f "${GROUP_COL_LIST}" ]; then
        PICRUSt_ARGS="${PICRUSt_ARGS} --group_col ${GROUP_COL_LIST}"
    fi
fi

if [ -n "${VENNG_LIST}" ] && [ -f "${VENNG_LIST}" ]; then
    PICRUSt_ARGS="${PICRUSt_ARGS} --fun_venn_group ${VENNG_LIST} --Group"
fi

# Step 2: 执行 PICRUSt2.pl
echo "[1/6] 执行 PICRUSt2 功能预测..."
"${PERL_BIN}" "${PICRUSt2_PL}" ${PICRUSt_ARGS} --outdir ./

# Step 3-6: 输出统计
echo ""
echo "✅ PICRUSt2 功能预测分析完成"
echo ""
echo "📊 输出文件:"
echo "   - EC_metagenome_out/: EC 酶功能预测结果"
echo "   - KO_metagenome_out/: KO 通路预测结果"
echo "   - pathways_out/: MetaCyc 通路预测结果"
if [ -d "fun_venn_group" ]; then
    echo "   - fun_venn_group/: 功能维恩图（分组）"
fi
echo ""

# 清理临时 BIOM 文件（如果是从 TSV 转换的）
if [[ "${INPUT_TABLE}" == *.tsv || "${INPUT_TABLE}" == *.txt ]]; then
    echo "🗑️  清理临时 BIOM 文件：${BIOM_TABLE}"
    rm -f "${BIOM_TABLE}"
fi
