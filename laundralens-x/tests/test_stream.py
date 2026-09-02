"""
Unit tests for Real-time Transaction Streaming API.
"""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_stream_recent_buffer():
    res = client.get("/api/v1/stream/recent?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert "buffer_capacity" in data
    assert isinstance(data["events"], list)
