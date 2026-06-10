#!/bin/bash
# step1_cutadapt.sh - Cutadapt 引物修剪脚本
# 用法：bash step1_cutadapt.sh -r1 <Sample.R1.fastq.gz> -r2 <Sample.R2.fastq.gz> -f <F_primer> -r <R_primer>

set -e

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
CUTADAPT_BIN="${CUTADAPT_BIN:-/software/anaconda3/envs/16s-env/bin/cutadapt}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
if [ ! -x "${CUTADAPT_BIN}" ]; then
    echo "❌ 错误：cutadapt 不存在：${CUTADAPT_BIN}"
    echo "   可通过环境变量 CUTADAPT_BIN 覆盖"
    echo "   示例：export CUTADAPT_BIN=\"/your/path/to/cutadapt\""
    exit 1
fi

R1_PATH=""
R2_PATH=""
F_PRIMER=""
R_PRIMER=""
ERROR_RATE="0.1"
MIN_LENGTH="100"
THREADS="1"

while [[ $# -gt 0 ]]; do
    case $1 in
        -r1|--r1-path) R1_PATH="$2"; shift 2 ;;
        -r2|--r2-path) R2_PATH="$2"; shift 2 ;;
        -f|--f-primer) F_PRIMER="$2"; shift 2 ;;
        -r|--r-primer) R_PRIMER="$2"; shift 2 ;;
        -e|--error-rate) ERROR_RATE="$2"; shift 2 ;;
        -l|--min-length) MIN_LENGTH="$2"; shift 2 ;;
        -n|--threads) THREADS="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step1_cutadapt.sh -r1 <Sample.R1.fastq.gz> -r2 <Sample.R2.fastq.gz> -f <F_primer> -r <R_primer>"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${R1_PATH}" ] && { echo "❌ 错误：必须提供 -r1"; exit 1; }
[ -z "${R2_PATH}" ] && { echo "❌ 错误：必须提供 -r2"; exit 1; }
[ -z "${F_PRIMER}" ] && { echo "❌ 错误：必须提供 -f"; exit 1; }
[ -z "${R_PRIMER}" ] && { echo "❌ 错误：必须提供 -r"; exit 1; }

# 检查输入文件
[ ! -f "${R1_PATH}" ] && { echo "❌ 错误：R1 文件不存在：${R1_PATH}"; exit 1; }
[ ! -f "${R2_PATH}" ] && { echo "❌ 错误：R2 文件不存在：${R2_PATH}"; exit 1; }

# 从文件名提取样本名 (去掉 .R1.fastq.gz 或 .R2.fastq.gz 后缀)
SAMPLE_NAME=$(basename "${R1_PATH}" | sed 's/\.R1\.fastq\.gz$//')

echo ""
echo "=========================================="
echo "Cutadapt 引物修剪"
echo "=========================================="
echo ""

echo "🔧 执行引物修剪..."
echo "   样本名：${SAMPLE_NAME}"
echo "   软件路径：${CUTADAPT_BIN}"
echo "   R1 输入：${R1_PATH}"
echo "   R2 输入：${R2_PATH}"
echo "   正向引物：${F_PRIMER}"
echo "   反向引物：${R_PRIMER}"
echo "   错误率：${ERROR_RATE}"
echo "   最小长度：${MIN_LENGTH}"
echo "   线程数：${THREADS}"

# 定义输出文件名 (带样本名)
OUTPUT_R1="${SAMPLE_NAME}.cutadapt.R1.fastq.gz"
OUTPUT_R2="${SAMPLE_NAME}.cutadapt.R2.fastq.gz"

# 执行 cutadapt
"${CUTADAPT_BIN}" \
    -g "${F_PRIMER}" \
    -G "${R_PRIMER}" \
    -e "${ERROR_RATE}" \
    --discard-untrimmed \
    --minimum-length "${MIN_LENGTH}" \
    -o "${OUTPUT_R1}" \
    -p "${OUTPUT_R2}" \
    "${R1_PATH}" \
    "${R2_PATH}"

echo "✅ Cutadapt 修剪完成"
echo ""
echo "📊 输出文件:"
echo "   - ${OUTPUT_R1}: 去除引物后的前向 fastq 数据"
echo "   - ${OUTPUT_R2}: 去除引物后的反向 fastq 数据"
echo ""
