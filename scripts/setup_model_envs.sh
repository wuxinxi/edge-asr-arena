#!/usr/bin/env bash

# ==============================================================================
# edge-asr-arena: 模型专属隔离虚拟环境初始化脚本 (.venvs/)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

UV_BIN="$(command -v uv || echo "/Users/sensiwu/.local/bin/uv")"
VENVS_DIR="${PROJECT_ROOT}/.venvs"
mkdir -p "${VENVS_DIR}"

setup_env() {
    local env_name="$1"
    local req_file="${PROJECT_ROOT}/scripts/model_requirements/requirements-${env_name}.txt"
    local target_venv="${VENVS_DIR}/${env_name}"
    local target_python="${target_venv}/bin/python"

    echo "=========================================================="
    echo "  🛠️  正在初始化专属环境: .venvs/${env_name}"
    echo "=========================================================="

    if [ ! -f "${req_file}" ]; then
        echo "❌ 依赖文件不存在: ${req_file}"
        exit 1
    fi

    if [ ! -d "${target_venv}" ]; then
        echo "⚡ 创建虚拟环境 .venvs/${env_name}..."
        "${UV_BIN}" venv --python "3.12" "${target_venv}"
    fi

    echo "📦 安装依赖项 (${req_file})..."
    "${UV_BIN}" pip install -r "${req_file}" --python "${target_python}" --default-index "https://mirrors.aliyun.com/pypi/simple"
    echo "✅ 环境准备完成: ${target_python}"
    echo "----------------------------------------------------------"
}

TARGET="${1:-funasr}"

if [ "${TARGET}" == "all" ]; then
    setup_env "funasr"
    setup_env "whisper"
    setup_env "qwen3asr"
else
    setup_env "${TARGET}"
fi

echo "🎉 目标环境安装完成！"
