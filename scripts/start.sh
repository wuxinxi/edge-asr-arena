#!/usr/bin/env bash

# ==============================================================================
# edge-asr-arena: 一键启动脚本
# 强制约定：必须使用项目根目录下的 .venv 虚拟环境
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

VENV_DIR="${PROJECT_ROOT}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"

if [ ! -f "${VENV_PYTHON}" ]; then
    echo "❌ 错误: 未找到本地虚拟环境 ${VENV_DIR}，请先运行 ./scripts/setup_env.sh 初始化环境！"
    exit 1
fi

echo "=========================================================="
echo "  🎙️  正在启动 edge-asr-arena 评测平台服务..."
echo "  💻 运行环境: $("${VENV_PYTHON}" --version)"
echo "=========================================================="

echo "⚡ 启动双进程开发模式 (FastAPI:8082 + Vite:5174)..."

# 启动 FastAPI 后端
"${VENV_PYTHON}" -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8082 --reload &
BACKEND_PID=$!

# 启动 Vite 前端
cd "${PROJECT_ROOT}/frontend"
npm run dev -- --port 5174 &
FRONTEND_PID=$!

echo ""
echo "🎉 edge-asr-arena 服务启动成功！"
echo "   🔗 前端界面 (Vue 3):    http://localhost:5174"
echo "   🔗 后端接口 (FastAPI):  http://localhost:8082"
echo "   📖 交互式 API 文档:     http://localhost:8082/docs"
echo ""
echo "按 Ctrl+C 即可退出所有服务..."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
