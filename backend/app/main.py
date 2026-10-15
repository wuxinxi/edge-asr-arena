"""
edge-asr-arena 后端 FastAPI 主服务入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.app.core.config import OUTPUTS_DIR, TESTSET_DIR
from backend.app.api.routes_system import router as system_router
from backend.app.api.routes_testset import router as testset_router
from backend.app.api.routes_compare import router as compare_router
from backend.app.api.routes_runs import router as runs_router

app = FastAPI(
    title="edge-asr-arena",
    description="PC 本地 ASR 能力探索与评测平台 API",
    version="1.0.0",
)

# 跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保静态目录存在
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
TESTSET_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态音频资源访问
app.mount("/api/audio/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs_audio")
app.mount("/api/audio/testset", StaticFiles(directory=str(TESTSET_DIR)), name="testset_audio")
app.mount("/api/audio", StaticFiles(directory=str(OUTPUTS_DIR)), name="audio_fallback")

# 注册 API 路由
app.include_router(system_router)
app.include_router(testset_router)
app.include_router(compare_router)
app.include_router(runs_router)


@app.get("/")
def index():
    return {
        "service": "edge-asr-arena",
        "status": "online",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8082, reload=True)
