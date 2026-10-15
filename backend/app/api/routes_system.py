"""
系统状态与模型列表 API
"""

import platform
import psutil
from fastapi import APIRouter
from typing import Dict, List, Any

from backend.app.core.config import MODELS_REGISTRY
from backend.app.core.model_files import check_model_availability

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/system")
def get_system_status() -> Dict[str, Any]:
    """获取系统运行环境与硬件状态"""
    vm = psutil.virtual_memory()
    return {
        "os": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "is_apple_silicon": platform.system() == "Darwin" and platform.machine() == "arm64",
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_total_gb": round(vm.total / (1024**3), 2),
        "memory_available_gb": round(vm.available / (1024**3), 2),
        "memory_used_percent": vm.percent,
    }


@router.get("/models")
def get_models() -> List[Dict[str, Any]]:
    """获取全部已注册的 ASR 模型列表及状态"""
    result = []
    for key, meta in MODELS_REGISTRY.items():
        is_avail, detail = check_model_availability(key)
        item = meta.model_dump()
        item["is_available"] = is_avail
        item["status_detail"] = detail
        result.append(item)
    return result
