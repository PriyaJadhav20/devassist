import pytest
from fastapi.testclient import TestClient

from devassist import server
from devassist.agent import Agent
from evals.dataset import _diff


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(server, "_agent", Agent())
    server._hits.clear()
    return TestClient(server.app)


def test_health_and_ui(client):
    assert client.get("/api/health").json()["status"] == "ok"
    page = client.get("/")
    assert "DevAssist" in page.text and "window.DEVASSIST_API" in page.text


def test_review_endpoint(client):
    r = client.post("/api/review", json={"diff": _diff("a.py", ["eval(x)"])})
    body = r.json()
    assert r.status_code == 200 and body["verdict"] == "changes_requested" and body["comments"][0]["line"] == 1


def test_validation_and_rate_limit(client):
    assert client.post("/api/review", json={"diff": ""}).status_code == 422
    codes = [client.post("/api/review", json={"diff": "x"}).status_code for _ in range(22)]
    assert codes[-1] == 429
