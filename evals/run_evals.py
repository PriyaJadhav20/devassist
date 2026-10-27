"""Measure recall, precision and latency. Add --llm to compare with the Claude agent."""
from __future__ import annotations

import argparse
import sys
import time

from devassist.agent import Agent
from devassist.heuristic import heuristic_review
from devassist.rag.retriever import Retriever
from devassist.static_checks import RULES
from evals.dataset import CASES

SEVERITY = {r.id: r.severity for r in RULES}


def score(review, expected: list[str], llm: bool) -> tuple[int, int, int]:
    """Rule mode matches rule ids. LLM mode matches severity, since the model does not emit rule ids."""
    if llm:
        want = [SEVERITY[e] for e in expected]
        got = [c.severity for c in review.comments if c.severity in ("security", "bug")]
        caught = sum(1 for sev in set(want) if sev in got)
        return caught, len(set(want)), len(got) if want else len(got)
    got_rules = {c.rule for c in review.comments if c.rule}
    return len(got_rules & set(expected)), len(expected), len(got_rules)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--llm", action="store_true")
    p.add_argument("--min-recall", type=float, default=0.9)
    p.add_argument("--min-precision", type=float, default=0.9)
    args = p.parse_args(argv)
    retriever = Retriever.from_dir()
    agent = Agent() if args.llm else None
    hit = total = reported = 0
    started = time.perf_counter()
    for case in CASES:
        review = agent.review(case["diff"]) if agent else heuristic_review(case["diff"], retriever)
        h, t, r = score(review, case["expected"], bool(agent))
        hit, total, reported = hit + h, total + t, reported + r
        print(f"{'ok ' if h == t and r == t else 'MISS'} {case['name']}: expected {t}, caught {h}, reported {r}")
    recall = hit / total if total else 1.0
    precision = hit / reported if reported else 1.0
    print(f"\nrecall={recall:.0%} precision={precision:.0%} cases={len(CASES)} "
          f"avg_latency={(time.perf_counter() - started) / len(CASES) * 1000:.1f}ms")
    return 0 if recall >= args.min_recall and precision >= args.min_precision else 1


if __name__ == "__main__":
    sys.exit(main())
