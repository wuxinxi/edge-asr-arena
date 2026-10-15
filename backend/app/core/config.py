"""
edge-asr-arena 平台配置与模型注册表
对齐 docs/models.md 与 docs/architecture.md
"""

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
CHECKPOINTS_DIR = PROJECT_ROOT / "checkpoints"
TESTSET_DIR = PROJECT_ROOT / "testset"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
VENVS_DIR = PROJECT_ROOT / ".venvs"


class ModelMetadata(BaseModel):
    """ASR 模型元数据"""
    key: str
    name: str
    family: str                          # whisper, qwen3asr, funasr, vibevoice
    parameters: str                      # 如 "809M", "0.6B"
    download_size: str                   # 如 "~1.6GB"
    license: str
    languages: List[str]                 # 如 ["zh", "en", "dialect"]
    supports_streaming: bool             # 是否支持流式 ASR
    supports_timestamps: bool = True     # 是否支持时间戳
    supports_emotion: bool = False       # 是否支持情感/音频事件
    mac_backend: str                     # 如 "mlx-whisper / faster-whisper", "MPS / bfloat16"
    recommended_device: str = "cpu"      # "cpu", "mps"
    repo_id: str                         # HuggingFace / ModelScope 标识
    venv_name: str                       # 对应的 .venvs 目录名


MODELS_REGISTRY: Dict[str, ModelMetadata] = {
    "whisper-turbo": ModelMetadata(
        key="whisper-turbo",
        name="OpenAI Whisper large-v3-turbo",
        family="whisper",
        parameters="809M",
        download_size="~1.6GB",
        license="MIT",
        languages=["zh", "en", "multilingual"],
        supports_streaming=False,
        supports_timestamps=True,
        mac_backend="mlx-whisper / faster-whisper",
        recommended_device="mps",
        repo_id="openai/whisper-large-v3-turbo",
        venv_name="whisper",
    ),
    "whisper-large-v3": ModelMetadata(
        key="whisper-large-v3",
        name="OpenAI Whisper large-v3",
        family="whisper",
        parameters="1.55B",
        download_size="~3.1GB",
        license="MIT",
        languages=["zh", "en", "multilingual"],
        supports_streaming=False,
        supports_timestamps=True,
        mac_backend="mlx-whisper / faster-whisper",
        recommended_device="mps",
        repo_id="openai/whisper-large-v3",
        venv_name="whisper",
    ),
    "qwen3-asr-0.6b": ModelMetadata(
        key="qwen3-asr-0.6b",
        name="Qwen3-ASR-0.6B-hf",
        family="qwen3asr",
        parameters="0.6B",
        download_size="~1.56GB",
        license="Apache 2.0",
        languages=["zh", "en", "dialect", "52-languages"],
        supports_streaming=True,
        supports_timestamps=True,
        mac_backend="transformers v5 / MPS",
        recommended_device="mps",
        repo_id="Qwen/Qwen3-ASR-0.6B-hf",
        venv_name="qwen3asr",
    ),
    "qwen3-asr-1.7b": ModelMetadata(
        key="qwen3-asr-1.7b",
        name="Qwen3-ASR-1.7B-hf",
        family="qwen3asr",
        parameters="1.7B",
        download_size="~4.08GB",
        license="Apache 2.0",
        languages=["zh", "en", "dialect", "52-languages"],
        supports_streaming=True,
        supports_timestamps=True,
        mac_backend="transformers v5 / MPS",
        recommended_device="mps",
        repo_id="Qwen/Qwen3-ASR-1.7B-hf",
        venv_name="qwen3asr",
    ),
    "sensevoice-small": ModelMetadata(
        key="sensevoice-small",
        name="FunAudioLLM/SenseVoiceSmall",
        family="funasr",
        parameters="234M",
        download_size="~460MB",
        license="Apache-like",
        languages=["zh", "en", "ja", "ko", "yue"],
        supports_streaming=False,
        supports_timestamps=True,
        supports_emotion=True,
        mac_backend="FunASR / CPU 实时",
        recommended_device="cpu",
        repo_id="FunAudioLLM/SenseVoiceSmall",
        venv_name="funasr",
    ),
    "paraformer-large": ModelMetadata(
        key="paraformer-large",
        name="paraformer-zh-large",
        family="funasr",
        parameters="220M",
        download_size="~840MB",
        license="Open Source",
        languages=["zh"],
        supports_streaming=False,
        supports_timestamps=True,
        mac_backend="FunASR / CPU 极速",
        recommended_device="cpu",
        repo_id="damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        venv_name="funasr",
    ),
    "paraformer-streaming": ModelMetadata(
        key="paraformer-streaming",
        name="paraformer-zh-streaming",
        family="funasr",
        parameters="220M",
        download_size="~840MB",
        license="Open Source",
        languages=["zh"],
        supports_streaming=True,
        supports_timestamps=True,
        mac_backend="FunASR / 低延迟流式",
        recommended_device="cpu",
        repo_id="damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online",
        venv_name="funasr",
    ),
    "fun-asr-nano": ModelMetadata(
        key="fun-asr-nano",
        name="Fun-ASR-Nano",
        family="funasr",
        parameters="800M",
        download_size="~3.2GB",
        license="Open Source",
        languages=["zh", "en", "ja", "dialect"],
        supports_streaming=False,
        supports_timestamps=True,
        mac_backend="FunASR LLM / CPU/MPS",
        recommended_device="mps",
        repo_id="FunAudioLLM/Fun-ASR-Nano-2512",
        venv_name="funasr",
    ),
    "fun-asr-mlt-nano": ModelMetadata(
        key="fun-asr-mlt-nano",
        name="Fun-ASR-MLT-Nano",
        family="funasr",
        parameters="800M",
        download_size="~3.2GB",
        license="Open Source",
        languages=["multilingual", "31-languages"],
        supports_streaming=True,
        supports_timestamps=True,
        mac_backend="FunASR / CPU/MPS",
        recommended_device="mps",
        repo_id="FunAudioLLM/Fun-ASR-MLT-Nano-2512",
        venv_name="funasr",
    ),
    "whisper-base": ModelMetadata(
        key="whisper-base",
        name="OpenAI Whisper base (faster-whisper)",
        family="whisper",
        parameters="74M",
        download_size="~145MB",
        license="MIT",
        languages=["zh", "en", "multilingual"],
        supports_streaming=False,
        supports_timestamps=True,
        mac_backend="faster-whisper / CPU 极速",
        recommended_device="cpu",
        repo_id="Systran/faster-whisper-base",
        venv_name="whisper",
    ),
}
