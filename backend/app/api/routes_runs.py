"""
单次转写能力探索与历史 API
"""

import time
import uuid
import shutil
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from backend.app.core.config import OUTPUTS_DIR
from backend.app.core.metrics import NormalizationConfig
from backend.app.adapters.factory import get_adapter
from backend.app.adapters.base import ASRTranscriptionResult

router = APIRouter(prefix="/api", tags=["runs"])

RUNS_STORE_FILE = OUTPUTS_DIR / "single_runs.json"


def _load_single_runs() -> List[Dict[str, Any]]:
    if not RUNS_STORE_FILE.exists():
        return []
    try:
        import json
        return json.loads(RUNS_STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_single_run(item: Dict[str, Any]):
    import json
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    runs = _load_single_runs()
    runs.insert(0, item)
    RUNS_STORE_FILE.write_text(json.dumps(runs, indent=2, ensure_ascii=False), encoding="utf-8")


@router.post("/asr/transcribe")
async def transcribe_audio(
    model_key: str = Form(...),
    language: str = Form("zh"),
    reference_text: Optional[str] = Form(None),
    audio_file: UploadFile = File(...),
) -> Dict[str, Any]:
    """上传音频并执行单模型转写（能力探索）"""
    run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # 严格限制仅支持音频文件格式
    ALLOWED_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
    audio_suffix = Path(audio_file.filename or "temp.wav").suffix.lower()
    if audio_suffix not in ALLOWED_AUDIO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"仅支持音频格式文件 ({', '.join(sorted(ALLOWED_AUDIO_EXTS))})，不支持视频文件或非音频格式 ({audio_suffix or '未知扩展名'})",
        )

    saved_audio_path = OUTPUTS_DIR / f"{run_id}{audio_suffix}"

    with saved_audio_path.open("wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)

    try:
        adapter = get_adapter(model_key)
        res: ASRTranscriptionResult = await asyncio.to_thread(
            adapter.transcribe,
            audio_path=str(saved_audio_path),
            reference_text=reference_text,
            language=language,
        )

        record = {
            "run_id": run_id,
            "model_key": model_key,
            "audio_file": f"/api/audio/outputs/{saved_audio_path.name}",
            "reference_text": reference_text,
            "result": res.model_dump(),
            "created_at": time.time(),
            "is_deleted": False,
        }
        _save_single_run(record)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
def list_runs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """分页获取单条转写历史"""
    runs = [r for r in _load_single_runs() if not r.get("is_deleted", False)]
    start = (page - 1) * limit
    end = start + limit
    return {
        "total": len(runs),
        "page": page,
        "limit": limit,
        "items": runs[start:end],
    }
