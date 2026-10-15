#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Whisper 系列模型 Worker (运行在 .venvs/whisper 中)
支持: whisper-large-v3, whisper-turbo
优先使用 faster-whisper CTranslate2 极速推理，并兼容 openai-whisper 原生权重
"""

import os
import sys
import json
import argparse
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

    lang_param = language if language != "auto" else None

    # 1. 如果存在 CTranslate2 权重 (model.bin)，优先使用 faster-whisper
    if (model_dir / "model.bin").exists():
        try:
            from faster_whisper import WhisperModel
            import soundfile as sf

            model = WhisperModel(
                str(model_dir),
                device="cpu",
                compute_type="int8",
            )
            audio_data, sr = sf.read(audio_file)

            segments_gen, info = model.transcribe(
                audio_data,
                language=lang_param,
                beam_size=5,
            )

            segments = []
            full_text = []
            for s in segments_gen:
                full_text.append(s.text.strip())
                segments.append({
                    "start": round(s.start, 3),
                    "end": round(s.end, 3),
                    "text": s.text.strip(),
                })

            return {
                "success": True,
                "text": "".join(full_text) if language == "zh" else " ".join(full_text),
                "language": info.language if info else language,
                "segments": segments,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"faster-whisper 执行失败: {e}",
            }

    # 2. 如果存在 safetensors 权重 (model.safetensors)，使用 Transformers 原生管线
    if (model_dir / "model.safetensors").exists():
        try:
            import torch
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

            device = "mps" if torch.backends.mps.is_available() else "cpu"
            dtype = torch.float16 if device == "mps" else torch.float32

            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                str(model_dir),
                torch_dtype=dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            ).to(device)
            processor = AutoProcessor.from_pretrained(str(model_dir))

            pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                torch_dtype=dtype,
                device=device,
                return_timestamps=True,
            )

            gen_kwargs = {}
            if lang_param:
                gen_kwargs["language"] = lang_param

            result = pipe(audio_file, generate_kwargs=gen_kwargs)
            chunks = result.get("chunks", [])
            segments = []
            for c in chunks:
                ts = c.get("timestamp") or (0.0, 0.0)
                segments.append({
                    "start": round(ts[0] or 0.0, 3),
                    "end": round(ts[1] or 0.0, 3),
                    "text": c.get("text", "").strip(),
                })

            return {
                "success": True,
                "text": result.get("text", "").strip(),
                "language": language,
                "segments": segments,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Transformers Whisper 执行失败: {e}",
            }

    # 3. 回退尝试 openai-whisper 原生 .pt 权重
    try:
        import whisper
        model = whisper.load_model(str(model_dir), device="cpu")
        result = model.transcribe(audio_file, language=lang_param)

        segments = [
            {
                "start": round(s.get("start", 0.0), 3),
                "end": round(s.get("end", 0.0), 3),
                "text": s.get("text", "").strip(),
            }
            for s in result.get("segments", [])
        ]

        return {
            "success": True,
            "text": result.get("text", "").strip(),
            "language": result.get("language", language),
            "segments": segments,
        }
    except Exception as py_err:
        return {
            "success": False,
            "error": f"原生 whisper 加载失败: {py_err}",
        }


def main():
    parser = argparse.ArgumentParser(description="Whisper Worker")
    parser.add_argument("--model-key", type=str, required=True, help="模型 key (如 whisper-large-v3)")
    parser.add_argument("--audio-file", type=str, required=True, help="输入音频文件路径")
    parser.add_argument("--language", type=str, default="zh", help="语言 (zh/en/auto)")

    args = parser.parse_args()
    result = run_transcription(args.model_key, args.audio_file, args.language)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
