"""
edge-asr-arena ASR 适配器工厂
"""

from typing import Dict
from backend.app.adapters.base import BaseASRAdapter
from backend.app.adapters.generic_worker_adapter import SubprocessASRAdapter
from backend.app.core.config import MODELS_REGISTRY


# 映射不同模型系列到其对应的 worker 脚本
WORKER_SCRIPT_MAPPING: Dict[str, str] = {
    "whisper": "whisper_worker.py",
    "funasr": "funasr_worker.py",
    "qwen3asr": "qwen3_worker.py",
}


def get_adapter(model_key: str) -> BaseASRAdapter:
    """获取对应模型的 ASR 适配器"""
    if model_key not in MODELS_REGISTRY:
        raise ValueError(f"未注册的模型: {model_key}")

    meta = MODELS_REGISTRY[model_key]
    script_name = WORKER_SCRIPT_MAPPING.get(meta.family, "whisper_worker.py")
    return SubprocessASRAdapter(model_key=model_key, worker_script_name=script_name)
