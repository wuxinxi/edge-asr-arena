#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FunASR 系列模型 Worker (运行在 .venvs/funasr 中)
支持: sensevoice-small, paraformer-large, paraformer-streaming
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# 保证能找到项目目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CHECKPOINTS_DIR = _PROJECT_ROOT / "checkpoints"


def parse_sensevoice_tags(raw_text: str):
    """从 SenseVoice 富文本标签中提取情感、音频事件与纯文本"""
    # 例如: <|zh|><|NEUTRAL|><|Speech|><|woitn|>今天天气真好
    emotion = None
    events = []
    
    # 匹配情感标签
    emotions = ["HAPPY", "SAD", "ANGRY", "NEUTRAL", "FEARFUL", "DISGUSTED", "SURPRISED"]
    for emo in emotions:
        if f"<|{emo}|>" in raw_text or f"<|{emo.lower()}|>" in raw_text:
            emotion = emo
            break

    # 匹配声音事件
    event_tags = ["LAUGHTER", "APPLAUSE", "COUGH", "SNEEZE", "CRY", "GIGGLE", "SNORT"]
    for ev in event_tags:
        if f"<|{ev}|>" in raw_text or f"<|{ev.lower()}|>" in raw_text:
            events.append(ev)

    # 剥离所有 <|...|> 格式的特殊标签以获取纯文本
    clean_text = re.sub(r"<\|[^|>]+\|>", "", raw_text).strip()
    return clean_text, emotion, events


def run_transcription(model_key: str, audio_file: str, language: str = "zh"):
    model_dir = _CHECKPOINTS_DIR / model_key
    if not model_dir.exists():
        return {
            "success": False,
            "error": f"模型权重目录不存在: {model_dir}",
        }

    try:
        from funasr import AutoModel
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
    except ImportError as e:
        return {
            "success": False,
            "error": f"FunASR 依赖未安装: {e}",
        }

    try:
        # FunASR 加载本地权重，优先 CPU 运行以确保稳定性和跨机型兼容
        model = AutoModel(
            model=str(model_dir),
            trust_remote_code=True,
            device="cpu",
            disable_update=True,
            disable_log=True,
        )

        lang_param = language if language != "auto" else "zh"
        if model_key == "sensevoice-small":
            res = model.generate(
                input=audio_file,
                cache={},
                language=lang_param,
                use_itn=True,
                batch_size_s=60,
            )
        else:
            res = model.generate(
                input=audio_file,
                batch_size_s=60,
            )

        if not res or len(res) == 0:
            return {
                "success": True,
                "text": "",
                "language": language,
                "segments": [],
            }

        raw_text = res[0].get("text", "")
        clean_text, emotion, audio_events = parse_sensevoice_tags(raw_text)

        # 尝试后处理
        try:
            processed_text = rich_transcription_postprocess(raw_text)
            if processed_text:
                clean_text = processed_text
        except Exception:
            pass

        # 解析时间戳
        segments = []
        raw_timestamps = res[0].get("timestamp", [])
        if raw_timestamps:
            for item in raw_timestamps:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    start_s = round(item[0] / 1000.0, 3) if item[0] > 100 else round(float(item[0]), 3)
                    end_s = round(item[1] / 1000.0, 3) if item[1] > 100 else round(float(item[1]), 3)
                    segments.append({"start": start_s, "end": end_s, "text": ""})

        return {
            "success": True,
            "text": clean_text,
            "language": language,
            "segments": segments,
            "emotion": emotion,
            "audio_events": audio_events,
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"{str(e)}\n{traceback.format_exc()}",
        }


def main():
    parser = argparse.ArgumentParser(description="FunASR Worker")
    parser.add_argument("--model-key", type=str, required=True, help="模型 key (如 sensevoice-small)")
    parser.add_argument("--audio-file", type=str, required=True, help="输入音频文件路径")
    parser.add_argument("--language", type=str, default="zh", help="语言 (zh/en/auto)")

    args = parser.parse_args()
    result = run_transcription(args.model_key, args.audio_file, args.language)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
