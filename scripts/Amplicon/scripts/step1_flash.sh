#!/bin/bash
# step1_flash.sh - FLASH 序列拼接脚本
# 用法：bash step1_flash.sh -1 <sample_R1.fastq.gz> -2 <sample_R2.fastq.gz> [-m min_overlap] [-M max_overlap] [-x max_ratio] [-t threads] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
# 默认路径（当前环境）
FLASH_BIN="${FLASH_BIN:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/01.Split/lib/FLASH-1.2.7/flash}"

# 如果设置了 MODULE_ENV_FILE，先加载配置文件
if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

# 验证软件存在
if [ ! -x "${FLASH_BIN}" ]; then
    echo "❌ 错误：flash 不存在：${FLASH_BIN}"
    echo "   可通过环境变量 FLASH_BIN 覆盖"
    echo "   示例：export FLASH_BIN=\"/your/path/to/flash\""
    exit 1
fi

R1_FASTQ=""
R2_FASTQ=""
MIN_OVERLAP="10"
MAX_OVERLAP="250"
MAX_RATIO="0.1"
THREADS="1"
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -1|--r1) R1_FASTQ="$2"; shift 2 ;;
        -2|--r2) R2_FASTQ="$2"; shift 2 ;;
        -m|--min-overlap) MIN_OVERLAP="$2"; shift 2 ;;
        -M|--max-overlap) MAX_OVERLAP="$2"; shift 2 ;;
        -x|--max-ratio) MAX_RATIO="$2"; shift 2 ;;
        -t|--threads) THREADS="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "用法：bash step1_flash.sh -1 <sample_R1.fastq.gz> -2 <sample_R2.fastq.gz> [-m min_overlap] [-M max_overlap] [-x max_ratio] [-t threads]"
            echo ""
            echo "参数:"
            echo "  -1, --r1           R1 测序文件"
            echo "  -2, --r2           R2 测序文件"
            echo "  -m, --min-overlap  最小重叠长度 (默认：10)"
            echo "  -M, --max-overlap  最大重叠长度 (默认：250)"
            echo "  -x, --max-ratio    最大错误率 (默认：0.1)"
            echo "  -t, --threads      线程数 (默认：1)"
            echo "  -o, --output     输出目录"

            echo "  -h, --help         显示帮助"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

# 参数验证
[ -z "${R1_FASTQ}" ] && { echo "❌ 错误：必须提供 -1"; exit 1; }
[ -z "${R2_FASTQ}" ] && { echo "❌ 错误：必须提供 -2"; exit 1; }

# 检查输入文件
[ ! -f "${R1_FASTQ}" ] && { echo "❌ 错误：R1 文件不存在：${R1_FASTQ}"; exit 1; }
[ ! -f "${R2_FASTQ}" ] && { echo "❌ 错误：R2 文件不存在：${R2_FASTQ}"; exit 1; }

[ -z "${OUTPUT_DIR}" ] && { echo "❌ 错误：必须提供 -o"; exit 1; }

# 从文件名提取样本名 (去掉 _R1.fastq.gz 或 _R2.fastq.gz 后缀)
SAMPLE_NAME=$(basename "${R1_FASTQ}" | sed 's/\.cutadapt.R1\.fastq\.gz$//')

echo ""
echo "=========================================="
echo "FLASH 序列拼接"
echo "=========================================="
echo ""

echo "🔧 执行序列拼接..."
echo "   样本名：${SAMPLE_NAME}"
echo "   软件路径：${FLASH_BIN}"
echo "   R1: ${R1_FASTQ}"
echo "   R2: ${R2_FASTQ}"
echo "   最小重叠：${MIN_OVERLAP}"
echo "   最大重叠：${MAX_OVERLAP}"
echo "   最大错误率：${MAX_RATIO}"
echo "   线程数：${THREADS}"

# ----- 路径转绝对路径（cd 输出目录前） -----
R1_FASTQ="$(abs_path_file "${R1_FASTQ}")"
R2_FASTQ="$(abs_path_file "${R2_FASTQ}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"
# ---------------------------------

mkdir -p "${OUTPUT_DIR}"

# 定义输出文件名 (带样本名)
OUTPUT_PREFIX="${OUTPUT_DIR}/${SAMPLE_NAME}"
FLASH_LOG="${OUTPUT_DIR}/${SAMPLE_NAME}.flash.log"

# 执行 FLASH 拼接
"${FLASH_BIN}" \
    "${R1_FASTQ}" \
    "${R2_FASTQ}" \
    -m ${MIN_OVERLAP} \
    -M ${MAX_OVERLAP} \
    -x ${MAX_RATIO} \
    -p 33 \
    -t ${THREADS} \
    -o "${OUTPUT_PREFIX}" \
    > "${FLASH_LOG}" 2>&1

echo "✅ FLASH 拼接完成"
echo ""
echo "📊 输出文件:"
echo "   - ${OUTPUT_PREFIX}.extendedFrags.fastq: 拼接后的序列"
echo "   - ${OUTPUT_PREFIX}.notCombined_1.fastq: 未拼接的正向序列"
echo "   - ${OUTPUT_PREFIX}.notCombined_2.fastq: 未拼接的反向序列"
echo "   - ${FLASH_LOG}: 拼接日志"
echo ""
