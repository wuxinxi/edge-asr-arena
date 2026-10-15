"""
测试集维度与音频列表 API
"""

import json
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from backend.app.core.config import TESTSET_DIR

router = APIRouter(prefix="/api/testset", tags=["testset"])


def _load_manifest() -> Dict[str, Any]:
    manifest_file = TESTSET_DIR / "manifest.json"
    if not manifest_file.exists():
        return {"dimensions": []}
    try:
        return json.loads(manifest_file.read_text(encoding="utf-8"))
    except Exception:
        return {"dimensions": []}


@router.get("/dimensions")
def get_dimensions() -> List[Dict[str, Any]]:
    """获取所有可用的评测维度列表"""
    data = _load_manifest()
    dims = data.get("dimensions", [])
    return [
        {
            "id": d.get("id"),
            "name": d.get("name"),
            "description": d.get("description"),
            "item_count": len(d.get("items", [])),
        }
        for d in dims
    ]


@router.get("/{dimension}")
def get_dimension_items(dimension: str) -> Dict[str, Any]:
    """获取指定维度的测试音频列表"""
    data = _load_manifest()
    for d in data.get("dimensions", []):
        if d.get("id") == dimension:
            return d
    raise HTTPException(status_code=404, detail=f"未找到评测维度: {dimension}")
