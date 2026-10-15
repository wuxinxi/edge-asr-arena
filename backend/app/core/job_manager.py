"""
edge-asr-arena 批次调度器与作业管理器
实现串行推理锁、任务队列管理与持久化
"""

import os
import json
import time
import uuid
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from backend.app.core.config import OUTPUTS_DIR, TESTSET_DIR, MODELS_REGISTRY
from backend.app.core.metrics import NormalizationConfig, compute_metrics, MetricsResult
from backend.app.adapters.factory import get_adapter
from backend.app.adapters.base import ASRTranscriptionResult


class JobTask(BaseModel):
    task_id: str
    model_key: str
    audio_file: str
    reference_text: Optional[str] = None
    language: str = "zh"
    repeat_index: int = 0
    status: str = "pending"   # pending, running, success, failed, stopped
    result: Optional[ASRTranscriptionResult] = None
    error: Optional[str] = None


class ASRJob(BaseModel):
    job_id: str
    dimension: str
    mode: str = "offline"     # offline, streaming
    repeats: int = 1
    model_keys: List[str]
    norm_config: NormalizationConfig = Field(default_factory=NormalizationConfig)
    tasks: List[JobTask] = Field(default_factory=list)
    total_tasks: int = 0
    completed_tasks: int = 0
    status: str = "pending"   # pending, running, completed, stopped, failed
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    is_deleted: bool = False


class JobManager:
    """全局作业调度器，具备全局串行推理锁"""

    def __init__(self):
        self._lock = threading.Lock()  # 全局串行推理锁
        self._jobs: Dict[str, ASRJob] = {}
        self._stop_flags: Dict[str, bool] = {}
        self._thread: Optional[threading.Thread] = None
        self._load_history()

    def _load_history(self):
        """从 outputs 目录载入已有批次快照，并对重启造成的孤儿任务进行自愈修复"""
        if not OUTPUTS_DIR.exists():
            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            return

        for job_file in OUTPUTS_DIR.glob("job_*.json"):
            try:
                data = json.loads(job_file.read_text(encoding="utf-8"))
                job = ASRJob(**data)
                # 自愈清理：若服务启动时发现任务残留为 running/pending/stopping，而实际已无运行线程
                if job.status in ("running", "stopping", "pending"):
                    if job.total_tasks > 0 and job.completed_tasks >= job.total_tasks:
                        job.status = "completed"
                    else:
                        job.status = "interrupted"
                        for t in job.tasks:
                            if t.status in ("running", "pending"):
                                t.status = "interrupted"
                                if not t.error:
                                    t.error = "服务重启导致任务中断"
                    self._save_job(job)
                self._jobs[job.job_id] = job
            except Exception:
                pass

    def _save_job(self, job: ASRJob):
        """保存批次快照"""
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        job_file = OUTPUTS_DIR / f"job_{job.job_id}.json"
        job_file.write_text(job.model_dump_json(indent=2), encoding="utf-8")

    def create_job(
        self,
        model_keys: List[str],
        dimension: str,
        testset_items: List[Dict[str, Any]],
        mode: str = "offline",
        repeats: int = 1,
        norm_config: Optional[NormalizationConfig] = None,
    ) -> ASRJob:
        job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        tasks: List[JobTask] = []

        cfg = norm_config or NormalizationConfig()

        for rep in range(repeats):
            for m_key in model_keys:
                for item in testset_items:
                    t_id = f"task_{uuid.uuid4().hex[:8]}"
                    tasks.append(
                        JobTask(
                            task_id=t_id,
                            model_key=m_key,
                            audio_file=item.get("audio_file", ""),
                            reference_text=item.get("reference_text"),
                            language=item.get("language", "zh"),
                            repeat_index=rep,
                        )
                    )

        job = ASRJob(
            job_id=job_id,
            dimension=dimension,
            mode=mode,
            repeats=repeats,
            model_keys=model_keys,
            norm_config=cfg,
            tasks=tasks,
            total_tasks=len(tasks),
            completed_tasks=0,
            status="pending",
        )

        self._jobs[job_id] = job
        self._stop_flags[job_id] = False
        self._save_job(job)

        # 启动后台工作线程串行执行
        t = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        t.start()

        return job

    def _run_job(self, job_id: str):
        job = self._jobs.get(job_id)
        if not job:
            return

        job.status = "running"
        job.updated_at = time.time()
        self._save_job(job)

        # 获取全局串行推理锁，确保一次只有一个模型转写在占用硬件
        with self._lock:
            for task in job.tasks:
                if self._stop_flags.get(job_id, False):
                    task.status = "stopped"
                    job.completed_tasks += 1
                    continue

                task.status = "running"
                job.updated_at = time.time()
                self._save_job(job)

                try:
                    adapter = get_adapter(task.model_key)
                    res = adapter.transcribe(
                        audio_path=task.audio_file,
                        reference_text=task.reference_text,
                        language=task.language,
                        norm_config=job.norm_config,
                    )
                    task.result = res
                    task.status = "success" if res.success else "failed"
                    if not res.success:
                        task.error = res.error
                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)

                job.completed_tasks += 1
                job.updated_at = time.time()
                self._save_job(job)

        if self._stop_flags.get(job_id, False):
            job.status = "stopped"
        else:
            job.status = "completed"
        job.updated_at = time.time()
        self._save_job(job)

    def stop_job(self, job_id: str) -> bool:
        if job_id in self._stop_flags:
            self._stop_flags[job_id] = True
            job = self._jobs.get(job_id)
            if job and job.status == "running":
                job.status = "stopping"
                self._save_job(job)
            return True
        return False

    def get_job(self, job_id: str) -> Optional[ASRJob]:
        return self._jobs.get(job_id)

    def get_active_job(self) -> Optional[ASRJob]:
        """获取当前正在执行的活跃作业（状态为 running 或 stopping）"""
        for j in self._jobs.values():
            if not j.is_deleted and j.status in ("running", "stopping"):
                return j
        return None

    def list_jobs(self, page: int = 1, limit: int = 10, include_deleted: bool = False) -> Dict[str, Any]:
        all_jobs = [
            j for j in self._jobs.values()
            if include_deleted or not j.is_deleted
        ]
        all_jobs.sort(key=lambda x: x.created_at, reverse=True)
        start = (page - 1) * limit
        end = start + limit
        return {
            "total": len(all_jobs),
            "page": page,
            "limit": limit,
            "items": all_jobs[start:end],
        }

    def delete_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.is_deleted = True
            job.updated_at = time.time()
            self._save_job(job)
            return True
        return False

    def restore_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.is_deleted = False
            job.updated_at = time.time()
            self._save_job(job)
            return True
        return False


# 全局单例
job_manager = JobManager()
