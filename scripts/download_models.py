#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
edge-asr-arena: 端侧主流 ASR 模型一键下载工具
- 支持 10 个主流端侧 ASR 模型
- 支持双下载源：ModelScope (魔搭社区，国内免翻墙高速直连) 与 Hugging Face (默认配置 hf-mirror.com)
- 智能跳过：检测到本地已存在有效权重文件时自动跳过，支持断点续传
- 环境守护：强制在项目本地 .venv 虚拟环境中运行
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------
# 虚拟环境自动守护：确保强制使用项目 .venv 运行
# ---------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_VENV_PYTHON = _PROJECT_ROOT / ".venv" / "bin" / "python"

if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
    try:
        import huggingface_hub
        import modelscope
    except ImportError:
        print(f"⚡ [环境守护] 检测到未在 .venv 中运行，自动切换解释器: {_VENV_PYTHON}")
        os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------
# 10 款 ASR 模型清单与仓库映射
# ---------------------------------------------------------
MODELS_DOWNLOAD_CONFIG: Dict[str, dict] = {
    "whisper-turbo": {
        "name": "OpenAI Whisper large-v3-turbo",
        "param_size": "809M",
        "download_size": "~1.6GB",
        "category": "生态基线 · 极速",
        "repo_id": "openai/whisper-large-v3-turbo",
        "ms_repo_id": "AI-ModelScope/whisper-large-v3-turbo",
        "desc": "解码器剪枝至 4 层，速度提升约 8 倍，Mac CPU/MPS 首选",
    },
    "whisper-large-v3": {
        "name": "OpenAI Whisper large-v3 (faster-whisper 满血版)",
        "param_size": "1.55B",
        "download_size": "~3.1GB",
        "category": "生态基线 · 精度上限",
        "repo_id": "Systran/faster-whisper-large-v3",
        "ms_repo_id": "Systran/faster-whisper-large-v3",
        "desc": "业界最高精度基线对照，多语言识别标杆",
    },
    "sensevoice-small": {
        "name": "FunAudioLLM/SenseVoiceSmall",
        "param_size": "234M",
        "download_size": "~460MB",
        "category": "中文极速 · 情感事件",
        "repo_id": "FunAudioLLM/SenseVoiceSmall",
        "ms_repo_id": "iic/SenseVoiceSmall",
        "desc": "中文 CER 7.81%，CPU 20x 实时，支持情感与富文本声音事件标签",
    },
    "paraformer-large": {
        "name": "paraformer-zh-large",
        "param_size": "220M",
        "download_size": "~840MB",
        "category": "工业落地 · CPU 极速",
        "repo_id": "funasr/paraformer-zh",
        "ms_repo_id": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
        "desc": "非自回归端到端，字级时间戳，CPU 22x 极速推理",
    },
    "paraformer-streaming": {
        "name": "paraformer-zh-streaming",
        "param_size": "220M",
        "download_size": "~840MB",
        "category": "工业落地 · 流式低延迟",
        "repo_id": "funasr/paraformer-zh-streaming",
        "ms_repo_id": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online",
        "desc": "低延迟块流式识别，中文会议与语音交互专用",
    },
    "fun-asr-nano": {
        "name": "Fun-ASR-Nano",
        "param_size": "800M",
        "download_size": "~3.2GB",
        "category": "LLM 解码 · 方言口音",
        "repo_id": "FunAudioLLM/Fun-ASR-Nano-2512",
        "ms_repo_id": "FunAudioLLM/Fun-ASR-Nano-2512",
        "desc": "LLM-ASR 架构，支持 7 大方言与 26 种地域口音",
    },
    "fun-asr-mlt-nano": {
        "name": "Fun-ASR-MLT-Nano",
        "param_size": "800M",
        "download_size": "~3.2GB",
        "category": "LLM 解码 · 31 多语言",
        "repo_id": "FunAudioLLM/Fun-ASR-MLT-Nano-2512",
        "ms_repo_id": "FunAudioLLM/Fun-ASR-MLT-Nano-2512",
        "desc": "Fun-ASR 多语言版本，覆盖 31 种全球语言",
    },
    "qwen3-asr-0.6b": {
        "name": "Qwen3-ASR-0.6B-hf",
        "param_size": "0.6B",
        "download_size": "~1.56GB",
        "category": "统一流式离线 · 22 方言",
        "repo_id": "Qwen/Qwen3-ASR-0.6B-hf",
        "ms_repo_id": "qwen/Qwen3-ASR-0.6B-hf",
        "desc": "2026 新星，52 语言 + 22 中文方言，统一流式与离线双路径",
    },
    "qwen3-asr-1.7b": {
        "name": "Qwen3-ASR-1.7B-hf",
        "param_size": "1.7B",
        "download_size": "~4.08GB",
        "category": "统一流式离线 · 旗舰上限",
        "repo_id": "Qwen/Qwen3-ASR-1.7B-hf",
        "ms_repo_id": "qwen/Qwen3-ASR-1.7B-hf",
        "desc": "Qwen3 满血版，极高方言理解度与长音频上下文理解",
    },
    "whisper-base": {
        "name": "OpenAI Whisper base (faster-whisper 极轻量版)",
        "param_size": "74M",
        "download_size": "~145MB",
        "category": "生态基线 · 极轻量",
        "repo_id": "Systran/faster-whisper-base",
        "ms_repo_id": "Systran/faster-whisper-base",
        "desc": "极轻量 74M 参数，CPU 秒级极速推理，极佳的小模型基线对照物",
    },
}

CHECKPOINTS_DIR = _PROJECT_ROOT / "checkpoints"


def is_model_downloaded(model_key: str) -> bool:
    """检查模型目录是否存在有效权重文件（必须包含实际模型权重而非仅配置）"""
    target_dir = CHECKPOINTS_DIR / model_key
    if not target_dir.exists():
        return False
    
    # 必须包含实质性的模型权重文件
    weight_patterns = ["*.bin", "*.safetensors", "*.pt", "*.pth", "*.gguf"]
    for pat in weight_patterns:
        # 支持一级目录或递归子目录检测
        if list(target_dir.glob(pat)) or list(target_dir.glob(f"**/{pat}")):
            return True
    return False


def download_from_modelscope(ms_repo_id: str, target_dir: Path) -> bool:
    """从魔搭社区下载"""
    try:
        from modelscope import snapshot_download
        print(f"🇨🇳 [ModelScope] 正在从魔搭社区直连拉取: {ms_repo_id}")
        target_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            model_id=ms_repo_id,
            local_dir=str(target_dir),
        )
        return True
    except Exception as e:
        print(f"❌ [ModelScope] 下载失败: {e}")
        return False


def download_from_huggingface(repo_id: str, target_dir: Path) -> bool:
    """从 HuggingFace 镜像源下载"""
    try:
        from huggingface_hub import snapshot_download
        # 默认注入国内 hf-mirror 镜像
        if "HF_ENDPOINT" not in os.environ:
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print(f"🌐 [Hugging Face] 正在拉取 (镜像源: {os.environ.get('HF_ENDPOINT')}): {repo_id}")
        target_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(target_dir),
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        return True
    except Exception as e:
        print(f"❌ [Hugging Face] 下载失败: {e}")
        return False


def download_model(model_key: str, source: str = "ms", force: bool = False) -> bool:
    """下载单个模型"""
    if model_key not in MODELS_DOWNLOAD_CONFIG:
        print(f"❌ 未知模型 key: {model_key}")
        return False

    cfg = MODELS_DOWNLOAD_CONFIG[model_key]
    target_dir = CHECKPOINTS_DIR / model_key

    print(f"\n=======================================================")
    print(f"📦 开始处理: {cfg['name']} ({cfg['param_size']}, {cfg['download_size']})")
    print(f"📁 目标目录: {target_dir}")
    print(f"=======================================================")

    if not force and is_model_downloaded(model_key):
        print(f"✅ 检测到本地已存在有效权重文件，自动跳过 (如需重新下载请加 --force)")
        return True

    success = False
    if source == "ms":
        # 优先魔搭
        success = download_from_modelscope(cfg["ms_repo_id"], target_dir)
        if not success:
            print("⚠️ ModelScope 拉取受阻，正在自动回退到 Hugging Face 镜像源...")
            success = download_from_huggingface(cfg["repo_id"], target_dir)
    else:
        # 优先 HF 镜像
        success = download_from_huggingface(cfg["repo_id"], target_dir)
        if not success:
            print("⚠️ Hugging Face 镜像拉取受阻，正在自动回退到 ModelScope...")
            success = download_from_modelscope(cfg["ms_repo_id"], target_dir)

    if success:
        print(f"🎉 成功完成: {model_key} 权重准备！")
    else:
        print(f"💥 下载失败: {model_key}")

    return success


def print_model_list():
    """打印模型清单状态表格"""
    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(title="edge-asr-arena 模型矩阵与下载状态", border_style="bright_blue")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("模型名称", style="white")
        table.add_column("参数量", style="magenta")
        table.add_column("体积", style="yellow")
        table.add_column("分类与场景", style="green")
        table.add_column("本地状态", style="bold")

        for key, cfg in MODELS_DOWNLOAD_CONFIG.items():
            downloaded = is_model_downloaded(key)
            status = "[green]✅ 已就绪[/green]" if downloaded else "[red]❌ 未下载[/red]"
            table.add_row(key, cfg["name"], cfg["param_size"], cfg["download_size"], cfg["category"], status)

        console.print(table)
    except ImportError:
        print(f"{'Key':<22} | {'参数':<6} | {'体积':<8} | {'状态'}")
        print("-" * 55)
        for key, cfg in MODELS_DOWNLOAD_CONFIG.items():
            downloaded = is_model_downloaded(key)
            status = "✅ 已就绪" if downloaded else "❌ 未下载"
            print(f"{key:<22} | {cfg['param_size']:<6} | {cfg['download_size']:<8} | {status}")


def main():
    parser = argparse.ArgumentParser(description="edge-asr-arena 模型一键下载工具")
    parser.add_argument("--list", action="store_true", help="查看所有支持的模型及本地下载状态")
    parser.add_argument("--model", type=str, help="指定要下载的模型 key (如 whisper-turbo)")
    parser.add_argument("--all", action="store_true", help="下载全部 10 款模型")
    parser.add_argument("--source", choices=["ms", "hf"], default="ms", help="首选下载源: ms (ModelScope) 或 hf (HuggingFace，默认 ms)")
    parser.add_argument("--force", action="store_true", help="强制重新下载，即使本地已有权重")

    args = parser.parse_args()

    if args.list:
        print_model_list()
        return

    if args.model:
        download_model(args.model, source=args.source, force=args.force)
    elif args.all:
        for key in MODELS_DOWNLOAD_CONFIG.keys():
            download_model(key, source=args.source, force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
