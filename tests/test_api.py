import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_system_status():
    resp = client.get("/api/system")
    assert resp.status_code == 200
    data = resp.json()
    assert "memory_total_gb" in data
    assert "is_apple_silicon" in data


def test_models_list():
    resp = client.get("/api/models")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 10
    keys = [m["key"] for m in data]
    assert "whisper-turbo" in keys
    assert "whisper-base" in keys
    assert "sensevoice-small" in keys
    assert "qwen3-asr-0.6b" in keys


def test_testset_dimensions():
    resp = client.get("/api/testset/dimensions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    dim_ids = [d["id"] for d in data]
    assert "01-mandarin" in dim_ids


def test_comparisons_history():
    resp = client.get("/api/comparisons?page=1&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
