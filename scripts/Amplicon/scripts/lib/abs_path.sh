#!/bin/bash
# abs_path.sh - 路径解析工具（v2 scripts 共用）
# 在 cd 输出目录之前调用，使 -i 等相对路径不受工作目录变化影响。

_abs_path_resolve() {
    local target="$1"
    if command -v realpath >/dev/null 2>&1; then
        realpath "${target}"
    elif readlink -f "${target}" >/dev/null 2>&1; then
        readlink -f "${target}"
    else
        local dir base
        dir="$(dirname "${target}")"
        base="$(basename "${target}")"
        dir="$(cd "${dir}" && pwd)"
        echo "${dir}/${base}"
    fi
}

# 已存在的文件 -> 绝对路径
abs_path_file() {
    local path="$1"
    [ -n "${path}" ] || return 1
    [ -f "${path}" ] || { echo "❌ 错误：文件不存在：${path}" >&2; return 1; }
    _abs_path_resolve "${path}"
}

# 已存在的目录 -> 绝对路径
abs_path_dir() {
    local path="$1"
    [ -n "${path}" ] || return 1
    [ -d "${path}" ] || { echo "❌ 错误：目录不存在：${path}" >&2; return 1; }
    if command -v realpath >/dev/null 2>&1; then
        realpath "${path}"
    else
        (cd "${path}" && pwd)
    fi
}

# 可选文件：空则原样返回空
abs_path_file_optional() {
    local path="$1"
    if [ -z "${path}" ]; then
        echo ""
        return 0
    fi
    abs_path_file "${path}"
}

# 可选目录
abs_path_dir_optional() {
    local path="$1"
    if [ -z "${path}" ]; then
        echo ""
        return 0
    fi
    abs_path_dir "${path}"
}

# 输出文件路径（文件可不存在，解析其目录为绝对路径）
abs_path_out_file() {
    local path="$1"
    local dir base
    dir="$(dirname "${path}")"
    base="$(basename "${path}")"
    if [ "${dir}" = "." ]; then
        echo "$(pwd)/${base}"
    else
        mkdir -p "${dir}"
        echo "$(cd "${dir}" && pwd)/${base}"
    fi
}

# 输出目录（可不存在）-> 绝对路径
abs_path_out_dir() {
    local path="$1"
    [ -n "${path}" ] || return 1
    if command -v realpath >/dev/null 2>&1; then
        realpath -m "${path}"
    elif [[ "${path}" = /* ]]; then
        echo "${path%/}"
    else
        local dir base
        dir="$(dirname "${path}")"
        base="$(basename "${path}")"
        if [ "${dir}" = "." ]; then
            echo "$(pwd)/${base}"
        else
            mkdir -p "${dir}"
            echo "$(cd "${dir}" && pwd)/${base}"
        fi
    fi
}
