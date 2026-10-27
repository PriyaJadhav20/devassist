"""FastAPI app: serves the web UI and a JSON review API."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import __version__
from .agent import Agent

WEB = Path(__file__).resolve().parent / "web" / "index.html"
RATE_LIMIT, WINDOW = 20, 60.0  # requests per client per minute
_hits: dict[str, deque[float]] = defaultdict(deque)
_agent: Agent | None = None

app = FastAPI(title="DevAssist", version=__version__)


class ReviewRequest(BaseModel):
    diff: str = Field(min_length=1, max_length=200_000)
    title: str = ""


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


def _check_rate(client: str) -> None:
    now = time.monotonic()
    q = _hits[client]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many reviews. Try again in a minute.")
    q.append(now)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "mode": get_agent().mode}


@app.post("/api/review")
def review(body: ReviewRequest, request: Request) -> dict:
    _check_rate(request.client.host if request.client else "unknown")
    result = get_agent().review(body.diff, body.title)
    return {**result.model_dump(), "verdict": result.verdict}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    page = WEB.read_text(encoding="utf-8")
    return page.replace("<!--DEVASSIST_API-->", '<script>window.DEVASSIST_API="/api/review"</script>')
