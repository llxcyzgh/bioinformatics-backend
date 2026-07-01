#!/bin/bash
# step4_simper.sh - SIMPER 相似性百分比分析脚本
# 用法：bash step4_simper.sh -i <Relative/|asv_table.even.txt> -g <group.list> [-l <levels>] [--top <N>] -o <output_dir>

set -e

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${_SCRIPT_DIR}/lib/abs_path.sh"

# ===== 软件路径（支持环境变量覆盖）=====
PERL_BIN="${PERL_BIN:-/usr/bin/perl}"
STAT_OTU_TAB_PL="${STAT_OTU_TAB_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/03.ASV/featureAnalysis/stat_otu_tab.pl}"
GET_SIMPER_PL="${GET_SIMPER_PL:-/newVol/users/guorongjun/work/Pipline/Amplicon_pipeline/Amplicon_pipeline_V1.0/lib/04.Taxa_visualization/lib/simper/get.simper.pl}"
RSCRIPT_BIN="${RSCRIPT_BIN:-/gfs/softwares/R/3.6.3/bin/Rscript}"
CONVERT_BIN="${CONVERT_BIN:-/usr/bin/convert}"

SIMPER_BIN="$(dirname "${GET_SIMPER_PL}")"

declare -A LEVEL_TO_CODE=(
    ["phylum"]="p"
    ["class"]="c"
    ["order"]="o"
    ["family"]="f"
    ["genus"]="g"
    ["species"]="s"
)
ALL_LEVELS=(otu phylum class order family genus species)

_parse_levels() {
    local input="$1"
    local token level
    declare -A seen=()
    SELECTED_LEVELS=()

    if [ -z "${input}" ]; then
        SELECTED_LEVELS=("${ALL_LEVELS[@]}")
        return 0
    fi

    local IFS=','
    for token in ${input}; do
        token="$(echo "${token}" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [ -z "${token}" ] && continue
        case "${token}" in
            otu|asv) level="otu" ;;
            phylum|p) level="phylum" ;;
            class|c) level="class" ;;
            order|o) level="order" ;;
            family|f) level="family" ;;
            genus|g) level="genus" ;;
            species|s) level="species" ;;
            *)
                echo "❌ 错误：未知分类层级：${token}"
                echo "   可选：otu, phylum(p), class(c), order(o), family(f), genus(g), species(s)"
                exit 1
                ;;
        esac
        if [ -z "${seen[$level]}" ]; then
            seen[$level]=1
            SELECTED_LEVELS+=("${level}")
        fi
    done

    if [ "${#SELECTED_LEVELS[@]}" -eq 0 ]; then
        echo "❌ 错误：-l 未指定有效分类层级"
        exit 1
    fi
}

# 去重同名分类单元（与 get.simper.pl 一致）
_dedupe_tax_table() {
    local infile="$1"
    local outfile="$2"
    "${PERL_BIN}" - "${infile}" "${outfile}" <<'PERL'
use strict;
my ($infile, $outfile) = @ARGV;
open my $in, '<', $infile or die $!;
open my $out, '>', $outfile or die $!;
my (@name, @num_name, $x);
while (<$in>) {
    chomp;
    my @l = split /\t/;
    $name[$x] = $l[0];
    $num_name[$x] = 0;
    for my $j (0 .. $x - 1) {
        if ($name[$x] eq $name[$j]) {
            $num_name[$x] += 1;
        }
    }
    my $a = join("\t", @l[1 .. $#l]);
    if ($num_name[$x] > 0) {
        print $out "$name[$x]_$num_name[$x]\t$a\n";
    } else {
        print $out "$name[$x]\t$a\n";
    }
    $x++;
}
close $in;
close $out;
PERL
}

_run_simper_level() {
    local level_name="$1"
    local rank_code="$2"
    local level_dir="${OUTPUT_DIR}/${level_name}"

    mkdir -p "${level_dir}"

    if [ "${level_name}" = "otu" ]; then
        local otufile="${RELATIVE_DIR}/asv_table.relative.xls"
        if [ ! -f "${otufile}" ]; then
            echo "  ⚠️  跳过 otu：未找到 ${otufile}"
            return 0
        fi
        cat > "${level_dir}/twork.sh" <<EOF
${RSCRIPT_BIN} ${SIMPER_BIN}/simper.R ${otufile} ${GROUP_FILE} ${TOP_N}
ls | grep pdf | awk 'BEGIN {FS=".pdf"}{print "${CONVERT_BIN} -density 200 " \$1 ".pdf " \$1 ".png"}' | sh
EOF
    else
        local infile="${RELATIVE_DIR}/asv_table.${rank_code}.relative.xls"
        if [ ! -f "${infile}" ]; then
            echo "  ⚠️  跳过 ${level_name}：未找到 ${infile}"
            return 0
        fi
        _dedupe_tax_table "${infile}" "${level_dir}/asv_table.${rank_code}.relative.xls"
        cat > "${level_dir}/twork.sh" <<EOF
${RSCRIPT_BIN} ${SIMPER_BIN}/simper.tax.R asv_table.${rank_code}.relative.xls ${GROUP_FILE} ${TOP_N}
ls | grep pdf | awk 'BEGIN {FS=".pdf"}{print "${CONVERT_BIN} -density 200 " \$1 ".pdf " \$1 ".png"}' | sh
EOF
    fi

    (cd "${level_dir}" && sh twork.sh)
    echo "  ✅ ${level_name} SIMPER 完成"
}

if [ -n "${MODULE_ENV_FILE}" ] && [ -f "${MODULE_ENV_FILE}" ]; then
    echo "📖 加载配置文件：${MODULE_ENV_FILE}"
    source "${MODULE_ENV_FILE}"
fi

if [ ! -x "${PERL_BIN}" ]; then
    echo "❌ 错误：PERL_BIN 不存在：${PERL_BIN}"
    exit 1
fi
if [ ! -f "${STAT_OTU_TAB_PL}" ]; then
    echo "❌ 错误：STAT_OTU_TAB_PL 不存在：${STAT_OTU_TAB_PL}"
    exit 1
fi
if [ ! -f "${GET_SIMPER_PL}" ]; then
    echo "❌ 错误：GET_SIMPER_PL 不存在：${GET_SIMPER_PL}"
    exit 1
fi
if [ ! -x "${RSCRIPT_BIN}" ]; then
    echo "❌ 错误：RSCRIPT_BIN 不存在：${RSCRIPT_BIN}"
    exit 1
fi

INPUT_PATH=""
GROUP_FILE=""
LEVELS_ARG=""
SELECTED_LEVELS=()
TOP_N="10"
OUTPUT_DIR=""
GENERATED_RELATIVE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input) INPUT_PATH="$2"; shift 2 ;;
        -g|--group) GROUP_FILE="$2"; shift 2 ;;
        -l|--levels) LEVELS_ARG="$2"; shift 2 ;;
        --top) TOP_N="$2"; shift 2 ;;
        -o|--output) OUTPUT_DIR="$2"; shift 2 ;;

        -h|--help)
            echo "用法：bash step4_simper.sh -i <Relative/|asv_table.even.txt> -g <group.list> [-l <levels>] [--top <N>] -o <output_dir>"
            echo ""
            echo "参数:"
            echo "  -i, --input      Relative/ 目录，或 step3 输出的 asv_table.even.txt"
            echo "  -g, --group      样本分组文件路径"
            echo "  -l, --levels     分析层级，逗号分隔（默认全部）"
            echo "  --top            Top 物种数量（默认：10）"
            echo "  -o, --output     输出目录"
            echo "  -h, --help       显示帮助"
            echo ""
            echo "层级可选：otu, phylum(p), class(c), order(o), family(f), genus(g), species(s)"
            echo "示例：-l phylum,genus  或  -l p,g"
            exit 0
            ;;
        *) echo "错误：未知参数 $1"; exit 1 ;;
    esac
done

if [ -z "${INPUT_PATH}" ]; then echo "❌ 错误：必须提供 -i"; exit 1; fi
if [ -z "${GROUP_FILE}" ]; then echo "❌ 错误：必须提供 -g"; exit 1; fi
if [ ! -f "${GROUP_FILE}" ]; then echo "❌ 错误：分组文件不存在：${GROUP_FILE}"; exit 1; fi
if [ -z "${OUTPUT_DIR}" ]; then echo "❌ 错误：必须提供 -o"; exit 1; fi
if [ ! -f "${INPUT_PATH}" ] && [ ! -d "${INPUT_PATH}" ]; then
    echo "❌ 错误：输入路径不存在：${INPUT_PATH}"
    echo "   -i 可传 Relative/ 目录或 asv_table.even.txt 文件"
    exit 1
fi

_parse_levels "${LEVELS_ARG}"

GROUP_FILE="$(abs_path_file "${GROUP_FILE}")"
OUTPUT_DIR="$(abs_path_out_dir "${OUTPUT_DIR}")"

# 在 cd 输出目录前解析 -i（避免相对路径在 cd 后失效）
if [ -f "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_file "${INPUT_PATH}")"
elif [ -d "${INPUT_PATH}" ]; then
    INPUT_PATH="$(abs_path_dir "${INPUT_PATH}")"
else
    echo "❌ 错误：无法识别输入：${INPUT_PATH}"
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"
cd "${OUTPUT_DIR}"

if [ -f "${INPUT_PATH}" ]; then
    EVEN_TABLE="${INPUT_PATH}"
    RELATIVE_DIR="${OUTPUT_DIR}/Relative"
    echo ""
    echo "=========================================="
    echo "SIMPER 相似性百分比分析"
    echo "=========================================="
    echo ""
    echo "📊 均一化 ASV 表：${EVEN_TABLE}"
    echo "[0/N] 生成 Relative 相对丰度表..."
    mkdir -p "${RELATIVE_DIR}"
    "${PERL_BIN}" "${STAT_OTU_TAB_PL}" \
        "${EVEN_TABLE}" \
        --prefix "${RELATIVE_DIR}/asv_table"
    echo "  ✅ Relative 目录：${RELATIVE_DIR}"
    GENERATED_RELATIVE=1
elif [ -d "${INPUT_PATH}" ]; then
    RELATIVE_DIR="${INPUT_PATH}"
else
    echo "❌ 错误：无法识别输入：${INPUT_PATH}"
    exit 1
fi

if [ ! -d "${RELATIVE_DIR}" ]; then
    echo "❌ 错误：相对丰度表目录不存在：${RELATIVE_DIR}"
    exit 1
fi

if [ "${GENERATED_RELATIVE}" -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "SIMPER 相似性百分比分析"
    echo "=========================================="
    echo ""
fi

echo "📊 相对丰度表目录：${RELATIVE_DIR}"
echo "📊 分组文件：${GROUP_FILE}"
echo "📊 Top 物种数量：${TOP_N}"
echo "📊 分析层级：$(IFS=,; echo "${SELECTED_LEVELS[*]}")"
echo ""

step=0
total="${#SELECTED_LEVELS[@]}"
for level in "${SELECTED_LEVELS[@]}"; do
    step=$((step + 1))
    echo "[${step}/${total}] ${level} 水平 SIMPER 分析..."
    if [ "${level}" = "otu" ]; then
        _run_simper_level "otu" ""
    else
        _run_simper_level "${level}" "${LEVEL_TO_CODE[$level]}"
    fi
done

echo ""
echo "✅ SIMPER 分析完成"
echo ""
echo "📊 输出文件:"
for level in "${SELECTED_LEVELS[@]}"; do
    echo "   - ${level}/simper_*.txt, ${level}/*.pdf/png: ${level} 水平 SIMPER 结果"
done
if [ "${GENERATED_RELATIVE}" -eq 1 ]; then
    echo "   - Relative/: 由 asv_table.even.txt 生成的相对丰度表"
fi
echo ""
