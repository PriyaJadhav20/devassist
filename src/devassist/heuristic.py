"""Offline reviewer: static checks plus guideline lookup. No API key needed."""
from __future__ import annotations

from .diff_parser import parse_diff
from .rag.retriever import Retriever
from .schemas import SEVERITY_ORDER, Review
from .static_checks import RULES, run_static_checks

MAX_COMMENTS = 10


def summarize(comments: list, mode_note: str = "") -> str:
    if not comments:
        return "No issues found in the changed lines. " + mode_note
    counts: dict[str, int] = {}
    for c in comments:
        counts[c.severity] = counts.get(c.severity, 0) + 1
    parts = ", ".join(f"{n} {sev}" for sev, n in sorted(counts.items(), key=lambda kv: SEVERITY_ORDER[kv[0]]))
    return f"Found {len(comments)} issue(s): {parts}. {mode_note}".strip()


def attach_guidelines(comments: list, retriever: Retriever) -> None:
    queries = {r.id: r.query for r in RULES}
    for c in comments:
        if c.guideline or not c.rule or c.rule not in queries:
            continue
        hits = retriever.search(queries[c.rule], k=1)
        if hits:
            c.guideline = hits[0].chunk.label


def heuristic_review(diff: str, retriever: Retriever | None = None) -> Review:
    retriever = retriever or Retriever.from_dir()
    comments = run_static_checks(parse_diff(diff))
    comments.sort(key=lambda c: (SEVERITY_ORDER[c.severity], c.file, c.line))
    comments = comments[:MAX_COMMENTS]
    attach_guidelines(comments, retriever)
    return Review(summary=summarize(comments, "(offline rule-based mode)"), comments=comments, mode="heuristic")
