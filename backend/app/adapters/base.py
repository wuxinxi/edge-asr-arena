"""
edge-asr-arena ASR 适配器基类与数据定义
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import time
import json
import subprocess
import psutil
import soundfile as sf

from backend.app.core.config import VENVS_DIR, MODELS_REGISTRY, ModelMetadata
from backend.app.core.metrics import compute_metrics, NormalizationConfig, MetricsResult


class ASRSegment(BaseModel):
    """时间戳分段"""
    start: float
    end: float
    text: str


class ASRTranscriptionResult(BaseModel):
    """单次转写执行结果"""
    success: bool
    text: str = ""
    language: str = "zh"
    segments: List[ASRSegment] = Field(default_factory=list)
    emotion: Optional[str] = None
    audio_events: List[str] = Field(default_factory=list)
    elapsed_ms: int = 0
    audio_duration_ms: int = 0
    rtf: float = 0.0
    memory_peak_mb: float = 0.0
    error: Optional[str] = None
    metrics: Optional[MetricsResult] = None


class BaseASRAdapter(ABC):
    """ASR 模型适配器抽象基类"""

    def __init__(self, model_key: str):
        if model_key not in MODELS_REGISTRY:
            raise ValueError(f"未注册的模型: {model_key}")
        self.model_key = model_key
        self.meta: ModelMetadata = MODELS_REGISTRY[model_key]
        self.venv_dir = VENVS_DIR / self.meta.venv_name
        self.venv_python = self.venv_dir / "bin" / "python"

    def get_audio_duration_ms(self, audio_path: str) -> int:
        """获取音频时长 (ms)"""
        try:
            info = sf.info(audio_path)
            return int(info.duration * 1000)
        except Exception:
            return 0

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        reference_text: Optional[str] = None,
        language: Optional[str] = None,
        norm_config: Optional[NormalizationConfig] = None,
    ) -> ASRTranscriptionResult:
        """执行离线转写"""
        pass
