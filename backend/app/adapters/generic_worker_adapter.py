"""
edge-asr-arena 通用子进程 Worker 适配器
通过独立虚拟环境执行 ASR 识别，隔离底层框架冲突与 OOM
"""

import os
import sys
import time
import json
import psutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

from backend.app.core.config import PROJECT_ROOT, VENVS_DIR, MODELS_REGISTRY, ModelMetadata
from backend.app.core.metrics import compute_metrics, NormalizationConfig, MetricsResult
from backend.app.adapters.base import BaseASRAdapter, ASRTranscriptionResult, ASRSegment


class SubprocessASRAdapter(BaseASRAdapter):
    """通过子进程运行模型 worker 脚本的通用适配器"""

    def __init__(self, model_key: str, worker_script_name: str):
        super().__init__(model_key)
        self.worker_script = PROJECT_ROOT / "backend" / "app" / "workers" / worker_script_name

    def transcribe(
        self,
        audio_path: str,
        reference_text: Optional[str] = None,
        language: Optional[str] = None,
        norm_config: Optional[NormalizationConfig] = None,
    ) -> ASRTranscriptionResult:
        duration_ms = self.get_audio_duration_ms(audio_path)
        
        # 优先使用模型专属虚拟环境的 Python，如果未单独创建则回退到平台 .venv
        python_exec = self.venv_python if self.venv_python.exists() else (PROJECT_ROOT / ".venv" / "bin" / "python")

        if not python_exec.exists():
            return ASRTranscriptionResult(
                success=False,
                audio_duration_ms=duration_ms,
                error=f"Python 解释器不存在: {python_exec}",
            )

        if not self.worker_script.exists():
            return ASRTranscriptionResult(
                success=False,
                audio_duration_ms=duration_ms,
                error=f"Worker 脚本不存在: {self.worker_script}",
            )

        cmd = [
            str(python_exec),
            str(self.worker_script),
            "--model-key", self.model_key,
            "--audio-file", audio_path,
        ]
        if language:
            cmd.extend(["--language", language])

        start_time = time.time()
        max_rss = 0

        try:
            # 启动子进程
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(PROJECT_ROOT),
            )

            # 采样 RSS 内存峰值 (字节 -> MB)
            try:
                p = psutil.Process(proc.pid)
                while proc.poll() is None:
                    try:
                        mem = p.memory_info().rss
                        # 包含子进程树内存
                        for child in p.children(recursive=True):
                            mem += child.memory_info().rss
                        if mem > max_rss:
                            max_rss = mem
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    time.sleep(0.05)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            stdout, stderr = proc.communicate(timeout=600)
            elapsed_ms = int((time.time() - start_time) * 1000)
            peak_mb = round(max_rss / (1024 * 1024), 2)

            if proc.returncode != 0:
                err_msg = stderr.strip() if stderr else f"Worker 异常退出，返回码 {proc.returncode}"
                return ASRTranscriptionResult(
                    success=False,
                    elapsed_ms=elapsed_ms,
                    audio_duration_ms=duration_ms,
                    memory_peak_mb=peak_mb,
                    error=err_msg,
                )

            # 解析 stdout 输出的 JSON
            # 找到输出中最后一行有效的 JSON
            json_line = None
            for line in reversed(stdout.strip().split("\n")):
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    json_line = line
                    break

            if not json_line:
                return ASRTranscriptionResult(
                    success=False,
                    elapsed_ms=elapsed_ms,
                    audio_duration_ms=duration_ms,
                    memory_peak_mb=peak_mb,
                    error=f"未能从 Worker 输出中解析 JSON: {stdout[:500]}",
                )

            data = json.loads(json_line)
            if not data.get("success", False):
                return ASRTranscriptionResult(
                    success=False,
                    elapsed_ms=elapsed_ms,
                    audio_duration_ms=duration_ms,
                    memory_peak_mb=peak_mb,
                    error=data.get("error", "Worker 执行未成功"),
                )

            transcribed_text = data.get("text", "")
            detected_lang = data.get("language", language or "zh")
            segments = [
                ASRSegment(start=s.get("start", 0.0), end=s.get("end", 0.0), text=s.get("text", ""))
                for s in data.get("segments", [])
            ]
            emotion = data.get("emotion")
            audio_events = data.get("audio_events", [])

            # 计算 RTF
            rtf = round(elapsed_ms / duration_ms, 4) if duration_ms > 0 else 0.0

            # 如果提供了参考文本，计算 CER/WER
            metrics = None
            if reference_text is not None:
                metrics = compute_metrics(
                    reference=reference_text,
                    hypothesis=transcribed_text,
                    norm_config=norm_config,
                    language=detected_lang,
                )

            return ASRTranscriptionResult(
                success=True,
                text=transcribed_text,
                language=detected_lang,
                segments=segments,
                emotion=emotion,
                audio_events=audio_events,
                elapsed_ms=elapsed_ms,
                audio_duration_ms=duration_ms,
                rtf=rtf,
                memory_peak_mb=peak_mb,
                metrics=metrics,
            )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return ASRTranscriptionResult(
                success=False,
                elapsed_ms=elapsed_ms,
                audio_duration_ms=duration_ms,
                error=str(e),
            )
