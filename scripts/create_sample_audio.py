"""
生成测试集真实人声语音音频 (16kHz 单声道 16-bit PCM WAV)
使用 macOS 原生高质量多语种语音合成器 (Tingting / Samantha) + ffmpeg
并在指定测试维度添加控制噪声 (如 06-noise)
"""

import os
import subprocess
import numpy as np
import soundfile as sf
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTSET_DIR = PROJECT_ROOT / "testset"

SAMPLES = [
    {
        "path": "01-mandarin/sample_mandarin_01.wav",
        "text": "今天的天气真不错，适合出门散步和运动。",
        "voice": "Tingting",
        "noise": 0.0,
    },
    {
        "path": "01-mandarin/sample_mandarin_02.wav",
        "text": "请在明天下午三点前把项目的最终报告提交给项目经理。",
        "voice": "Tingting",
        "noise": 0.0,
    },
    {
        "path": "02-english/sample_english_01.wav",
        "text": "the quick brown fox jumps over the lazy dog",
        "voice": "Samantha",
        "noise": 0.0,
    },
    {
        "path": "04-code-switch/sample_cs_01.wav",
        "text": "请把这个 PR 合并到 main 分支，然后跑一下 build 测试。",
        "voice": "Tingting",
        "noise": 0.0,
    },
    {
        "path": "06-noise/sample_noise_01.wav",
        "text": "我们在嘈杂的咖啡厅里讨论下个季度的产品研发规划。",
        "voice": "Tingting",
        "noise": 0.06,  # 添加背景噪声
    },
    {
        "path": "08-numbers/sample_numbers_01.wav",
        "text": "我的联系电话是13800138000，订单编号为ABC20261013。",
        "voice": "Tingting",
        "noise": 0.0,
    },
    {
        "path": "09-emotion/sample_emotion_01.wav",
        "text": "哈哈，太好笑了，我完全没想到结果会是这样！",
        "voice": "Tingting",
        "noise": 0.0,
    },
]


def generate_speech_wav(target_path: Path, text: str, voice: str, noise_level: float = 0.0):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_aiff = Path(f"/tmp/temp_say_{target_path.stem}.aiff")
    temp_wav = Path(f"/tmp/temp_conv_{target_path.stem}.wav")

    try:
        # 1. 采用 macOS say 工具合成高质量原始音频
        subprocess.run(
            ["/usr/bin/say", "-v", voice, text, "-o", str(temp_aiff)],
            check=True,
            capture_output=True,
        )

        # 2. 通过 ffmpeg 重采样为标准的 16kHz 单声道 WAV
        subprocess.run(
            [
                "/opt/homebrew/bin/ffmpeg",
                "-y",
                "-i", str(temp_aiff),
                "-ar", "16000",
                "-ac", "1",
                str(temp_wav),
            ],
            check=True,
            capture_output=True,
        )

        # 3. 读取并按需叠加噪声
        audio_data, sr = sf.read(str(temp_wav))
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, audio_data.shape)
            audio_data = np.clip(audio_data + noise, -1.0, 1.0)

        # 保存为目标文件
        sf.write(str(target_path), audio_data, sr, subtype="PCM_16")

        dur = len(audio_data) / sr
        print(f"✅ 生成人声真实音频: {target_path.name} ({dur:.2f}s, voice={voice}, noise={noise_level})")

    finally:
        if temp_aiff.exists():
            temp_aiff.unlink()
        if temp_wav.exists():
            temp_wav.unlink()


def main():
    print("🎙️ 开始生成测试集人声真实语音...")
    for item in SAMPLES:
        target = TESTSET_DIR / item["path"]
        generate_speech_wav(target, item["text"], item["voice"], item["noise"])
    print("🎉 测试集真实音频生成完毕！")


if __name__ == "__main__":
    main()
