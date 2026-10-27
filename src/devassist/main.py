from __future__ import annotations

import argparse
import logging
import os
import sys

from .agent import Agent
from .github_client import GitHubClient
from .report import to_markdown


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="devassist", description="AI code review agent")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("review", help="review a GitHub pull request")
    pr.add_argument("--repo", required=True, help="owner/name")
    pr.add_argument("--pr", type=int, required=True)
    pr.add_argument("--dry-run", action="store_true", help="print instead of posting")
    df = sub.add_parser("review-diff", help="review a local .diff file (use - for stdin)")
    df.add_argument("path")
    sub.add_parser("serve", help="start the web UI and API").add_argument("--port", type=int, default=8000)
    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("devassist.server:app", host="0.0.0.0", port=args.port)
        return 0
    agent = Agent()
    if args.cmd == "review-diff":
        diff = sys.stdin.read() if args.path == "-" else open(args.path, encoding="utf-8").read()
        print(to_markdown(agent.review(diff)))
        return 0
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("error: set GITHUB_TOKEN", file=sys.stderr)
        return 2
    gh = GitHubClient(token)
    pr = gh.get_pr(args.repo, args.pr)
    review = agent.review(gh.get_pr_diff(args.repo, args.pr), title=pr.get("title", ""))
    print(to_markdown(review))
    if not args.dry_run:
        print(f"posted as {gh.post_review(args.repo, args.pr, review)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
