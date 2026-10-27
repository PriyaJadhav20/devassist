from __future__ import annotations

import logging

import requests

from .report import format_comment, to_markdown
from .schemas import Review

log = logging.getLogger("devassist")


class GitHubClient:
    def __init__(self, token: str, api: str = "https://api.github.com") -> None:
        self.api = api.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"})

    def get_pr(self, repo: str, number: int) -> dict:
        r = self.session.get(f"{self.api}/repos/{repo}/pulls/{number}", timeout=30)
        r.raise_for_status()
        return r.json()

    def get_pr_diff(self, repo: str, number: int) -> str:
        r = self.session.get(f"{self.api}/repos/{repo}/pulls/{number}",
                             headers={"Accept": "application/vnd.github.v3.diff"}, timeout=30)
        r.raise_for_status()
        return r.text

    def post_review(self, repo: str, number: int, review: Review) -> str:
        """Post inline comments; fall back to one summary comment if GitHub rejects a position."""
        payload = {"body": f"**DevAssist**: {review.summary}", "event": "COMMENT",
                   "comments": [{"path": c.file, "line": c.line, "side": "RIGHT", "body": format_comment(c)}
                                for c in review.comments]}
        r = self.session.post(f"{self.api}/repos/{repo}/pulls/{number}/reviews", json=payload, timeout=30)
        if r.status_code < 300:
            return "review"
        log.warning("inline review rejected (%s); posting summary comment", r.status_code)
        r = self.session.post(f"{self.api}/repos/{repo}/issues/{number}/comments",
                              json={"body": to_markdown(review)}, timeout=30)
        r.raise_for_status()
        return "comment"
