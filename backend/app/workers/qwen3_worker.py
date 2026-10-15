#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Qwen3-ASR 系列模型 Worker (运行在 .venvs/qwen3asr 中)
支持: qwen3-asr-0.6b, qwen3-asr-1.7b
统一流式与离线双路径，支持 52 种语言与 22 种中文方言
"""

import os
import sys
import json
import argparse
import soundfile as sf
import torch
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CHECKPOINTS_DIR = _PROJECT_ROOT / "checkpoints"


def run_transcription(model_key: str, audio_file: str, language: str = "zh"):
    model_dir = _CHECKPOINTS_DIR / model_key
    if not model_dir.exists():
        return {
            "success": False,
            "error": f"模型权重目录不存在: {model_dir}",
        }

    try:
        from transformers import AutoModelForMultimodalLM, AutoProcessor
    except ImportError as e:
        return {
            "success": False,
            "error": f"Transformers 依赖未安装: {e}",
        }

    try:
        # 检测设备：Apple Silicon MPS 或 CPU
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        dtype = torch.bfloat16 if device == "mps" else torch.float32

        processor = AutoProcessor.from_pretrained(str(model_dir))
        model = AutoModelForMultimodalLM.from_pretrained(
            str(model_dir),
            torch_dtype=dtype,
            device_map=device,
        )

        audio_data, sr = sf.read(audio_file)
        if sr != 16000:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)

        # 构造输入: Qwen3-ASR 官方规范 apply_transcription_request
        kwargs = {"audio": audio_data}
        if language and language != "auto":
            lang_map = {"zh": "Chinese", "en": "English", "yue": "Cantonese"}
            kwargs["language"] = lang_map.get(language, language)

        inputs = processor.apply_transcription_request(**kwargs)
        inputs = inputs.to(device=model.device, dtype=model.dtype)

        with torch.no_grad():
            output_ids = model.generate(**inputs, max_new_tokens=256)
            generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]

        transcription = processor.decode(generated_ids, return_format="transcription_only")[0]

        return {
            "success": True,
            "text": transcription.strip(),
            "language": language,
            "segments": [],
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"{str(e)}\n{traceback.format_exc()}",
        }


def main():
    parser = argparse.ArgumentParser(description="Qwen3-ASR Worker")
    parser.add_argument("--model-key", type=str, required=True, help="模型 key (如 qwen3-asr-0.6b)")
    parser.add_argument("--audio-file", type=str, required=True, help="输入音频文件路径")
    parser.add_argument("--language", type=str, default="zh", help="语言 (zh/en/auto)")

    args = parser.parse_args()
    result = run_transcription(args.model_key, args.audio_file, args.language)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
