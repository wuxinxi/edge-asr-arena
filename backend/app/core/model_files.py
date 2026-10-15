"""
edge-asr-arena 模型权重文件完整性校验
"""

from pathlib import Path
from typing import Dict, List, Tuple
from backend.app.core.config import CHECKPOINTS_DIR, MODELS_REGISTRY, ModelMetadata


def get_model_checkpoint_dir(model_key: str) -> Path:
    """获取模型存放目录"""
    return CHECKPOINTS_DIR / model_key


def check_model_availability(model_key: str) -> Tuple[bool, str]:
    """
    检查模型权重是否准备就绪
    返回: (is_available, detail_message)
    """
    if model_key not in MODELS_REGISTRY:
        return False, f"未知模型 key: {model_key}"

    meta = MODELS_REGISTRY[model_key]
    model_dir = get_model_checkpoint_dir(model_key)

    if not model_dir.exists():
        return False, f"权重目录不存在: {model_dir}"

    # 简单检查是否有权重文件
    has_weights = any(
        model_dir.glob("*.bin")
    ) or any(
        model_dir.glob("*.safetensors")
    ) or any(
        model_dir.glob("*.gguf")
    ) or any(
        model_dir.glob("model.pt")
    ) or (model_dir / "config.json").exists()

    if not has_weights:
        return False, f"目录中未找到权重文件 (bin/safetensors/gguf/config.json): {model_dir}"

    return True, "已就绪"
