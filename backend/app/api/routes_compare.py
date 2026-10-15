"""
ASR 批次对比与历史管理 API
"""

import json
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

from backend.app.core.config import TESTSET_DIR
from backend.app.core.metrics import NormalizationConfig
from backend.app.core.job_manager import job_manager, ASRJob

router = APIRouter(prefix="/api", tags=["compare"])


class CreateJobRequest(BaseModel):
    model_keys: List[str]
    dimension: str
    mode: str = "offline"     # offline, streaming
    repeats: int = 1
    norm_config: Optional[NormalizationConfig] = None


@router.post("/asr/compare/jobs")
def create_compare_job(req: CreateJobRequest) -> Dict[str, Any]:
    """创建并启动 ASR 评测批次"""
    manifest_file = TESTSET_DIR / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=400, detail="测试集 manifest.json 不存在")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    target_dim = None
    for d in manifest.get("dimensions", []):
        if d.get("id") == req.dimension:
            target_dim = d
            break

    if not target_dim:
        raise HTTPException(status_code=404, detail=f"未找到指定的测试维度: {req.dimension}")

    items = []
    for item in target_dim.get("items", []):
        audio_rel = item.get("filename")
        audio_abs = TESTSET_DIR / audio_rel
        items.append({
            "audio_file": str(audio_abs),
            "reference_text": item.get("reference_text"),
            "language": item.get("language", "zh"),
            "item_id": item.get("id"),
        })

    job = job_manager.create_job(
        model_keys=req.model_keys,
        dimension=req.dimension,
        testset_items=items,
        mode=req.mode,
        repeats=req.repeats,
        norm_config=req.norm_config,
    )

    return {"job_id": job.job_id, "status": job.status, "total_tasks": job.total_tasks}


@router.get("/asr/compare/active-job")
def get_active_compare_job() -> Optional[Dict[str, Any]]:
    """获取当前正在执行的活跃评测作业（如有）"""
    job = job_manager.get_active_job()
    if job:
        return job.model_dump()
    return None


@router.get("/asr/compare/jobs/{job_id}")
def get_compare_job(job_id: str) -> Dict[str, Any]:
    """查询批次详情与实时进度"""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"未找到批次: {job_id}")
    return job.model_dump()


@router.post("/asr/compare/jobs/{job_id}/stop")
def stop_compare_job(job_id: str) -> Dict[str, Any]:
    """停止批次中尚未执行的任务"""
    success = job_manager.stop_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"未找到批次: {job_id}")
    return {"success": True, "message": "已发送停止信号"}


@router.get("/comparisons")
def list_comparisons(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    include_deleted: bool = False,
) -> Dict[str, Any]:
    """分页获取批次历史列表"""
    return job_manager.list_jobs(page=page, limit=limit, include_deleted=include_deleted)


@router.delete("/comparisons/{job_id}")
def delete_comparison(job_id: str) -> Dict[str, Any]:
    """将批次移入回收站（软删除）"""
    success = job_manager.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"未找到批次: {job_id}")
    return {"success": True}


@router.post("/comparisons/{job_id}/restore")
def restore_comparison(job_id: str) -> Dict[str, Any]:
    """从回收站恢复批次"""
    success = job_manager.restore_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"未找到批次: {job_id}")
    return {"success": True}
