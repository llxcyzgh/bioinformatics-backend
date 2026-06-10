#!/bin/bash
# step2_frags_qc.sh - Frags_QC 质量控制脚本
# 用法：bash step2_frags_qc.sh -i <sample.extendedFrags.fastq> [-q quality] [-u max_n] [-d ref_db]

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
FASTP_BIN="${FASTP_BIN:-/software/anaconda3/envs/prokka/bin/fastp}"
VSEARCH_BIN="${VSEARCH_BIN:-/software/anaconda3/pkgs/vsearch-2.7.0-1/bin/vsearch}"
NG_QC_BIN="${NG_QC_BIN:-/gfs/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/software/qc/ng_QC}"
SELECT_FQ_IN_FA_PL="${SELECT_FQ_IN_FA_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/02.FragsQC/lib/Select_FqInFa.pl}"
LINE_DIAGRAM_PL="${LINE_DIAGRAM_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/02.FragsQC/lib/line_diagram.pl}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
for bin in FASTP_BIN VSEARCH_BIN NG_QC_BIN SELECT_FQ_IN_FA_PL LINE_DIAGRAM_PL CONVERT_BIN; do
    if [ ! -x "${!bin}" ]; then
        echo "❌ 错误：${bin} 不存在：${!bin}"
        echo "   可通过环境变量覆盖，例如：export ${bin}=\"/your/path/to/${bin}\""
        exit 1
    fi
done

INPUT_FASTQ=""
QUALITY="19"
MAX_N="15"
REF_DB=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_FASTQ="$2"; shift 2 ;;
        -q|--quality) QUALITY="$2"; shift 2 ;;
        -u|--max-n) MAX_N="$2"; shift 2 ;;
        -d|--ref-db) REF_DB="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step2_frags_qc.sh -i <sample.extendedFrags.fastq> [-q quality] [-u max_n] [-d ref_db]"
            echo ""
            echo "参数:"
            echo "  -i, --input      输入 FASTQ 文件"
            echo "  -q, --quality    质量阈值 (默认：19)"
            echo "  -u, --max-n      最大 N 比例 (默认：15)"
            echo "  -d, --ref-db     参考数据库 (可选)"
            echo "  -h, --help       显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${INPUT_FASTQ}" ] && { echo "❌ 错误：必须提供 -i"; exit 1; }
[ ! -f "${INPUT_FASTQ}" ] && { echo "❌ 错误：输入文件不存在：${INPUT_FASTQ}"; exit 1; }

# 从文件名提取样本名 (去掉 .extendedFrags.fastq 后缀)
SAMPLE_NAME=$(basename "${INPUT_FASTQ}" | sed 's/\.extendedFrags\.fastq$//')

echo ""
echo "=========================================="
echo "Frags_QC 质量控制"
echo "=========================================="
echo ""

echo "🔧 执行质量控制..."
echo "   样本名：${SAMPLE_NAME}"
echo "   输入文件：${INPUT_FASTQ}"
echo "   质量阈值：${QUALITY}"
echo "   最大 N 比例：${MAX_N}"
echo ""

# Step 1: fastp 质量过滤
echo "[1/6] fastp 质量过滤..."
"${FASTP_BIN}" \
    -i "${INPUT_FASTQ}" \
    -o "${SAMPLE_NAME}.clean.fq.gz" \
    -A -g \
    -q ${QUALITY} \
    -u ${MAX_N} \
    -j "${SAMPLE_NAME}.json" \
    -h "${SAMPLE_NAME}.html"

# Step 2: 格式转换
echo "[2/6] 格式转换..."
zcat "${SAMPLE_NAME}.clean.fq.gz" | \
    sed "1~4s=@=@${SAMPLE_NAME} =g" | \
    awk 'NR%4==1{{ $1=$1"_"int(NR/4)+1;print $0 }} NR%4!=1{{ print $0 }}' > seqs.fastq

awk 'NR%4>0 && NR%4<3{{ print $1 }}' seqs.fastq | \
    sed "s=@=>=g" > seqs.fna

# Step 3: 去嵌合体
echo "[3/6] VSEARCH 去嵌合体..."
if [ -n "${REF_DB}" ] && [ -f "${REF_DB}" ]; then
    "${VSEARCH_BIN}" \
        -uchime_ref seqs.fna \
        -db "${REF_DB}" \
        -nonchimeras seqs.nonchimeras.fna
else
    echo "⚠️  未提供参考数据库，跳过嵌合体去除"
    cp seqs.fna seqs.nonchimeras.fna
fi

# Step 4: 提取序列
echo "[4/6] 提取非嵌合体序列..."
perl "${SELECT_FQ_IN_FA_PL}" \
    "${SAMPLE_NAME}.clean.fq.gz" \
    seqs.nonchimeras.fna \
    seqs.nonchimeras.fastq

mv -f seqs.nonchimeras.fastq "${SAMPLE_NAME}.fastq"
mv -f seqs.nonchimeras.fna "${SAMPLE_NAME}.fna"

# Step 5: 长度分布图
echo "[5/6] 生成序列长度分布图..."
perl "${LINE_DIAGRAM_PL}" \
    --fasta --fredb -bar \
    -x_title "Reads Length(nt)" \
    -y_title "Reads Number(#)" \
    --windl 1 --frame --gridy --numberc \
    "${SAMPLE_NAME}.fna" > "${SAMPLE_NAME}.fna.histograms.svg"

"${CONVERT_BIN}" "${SAMPLE_NAME}.fna.histograms.svg" "${SAMPLE_NAME}.fna.histograms.png"

# Step 6: 质控报告
echo "[6/6] 生成详细质控报告..."
"${NG_QC_BIN}" \
    -i "${SAMPLE_NAME}.fastq" \
    -N 1 -q 33 -L 5 -p 1 \
    -o ng_QC

# 清理临时文件
rm -f seqs.fastq seqs.fna seqs.nonchimeras.fna "${SAMPLE_NAME}.clean.fq.gz" "${SAMPLE_NAME}.fna.histograms.svg"

echo ""
echo "✅ Frags_QC 质量控制完成"
echo ""
echo "📊 输出文件:"
echo "   - ${SAMPLE_NAME}.fastq: 质控后序列"
echo "   - ${SAMPLE_NAME}.fna: 质控后核酸序列"
echo "   - ${SAMPLE_NAME}.json: fastp 质控统计"
echo "   - ${SAMPLE_NAME}.html: fastp 质控报告"
echo "   - ${SAMPLE_NAME}.fna.histograms.png: 序列长度分布图"
echo "   - ng_QC/: 详细质控统计目录"
echo ""
