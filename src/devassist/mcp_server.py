"""MCP server: use DevAssist from Claude Desktop or any MCP client."""
from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .agent import Agent
from .github_client import GitHubClient
from .report import to_markdown

mcp = FastMCP("devassist")
_agent = Agent()


@mcp.tool()
def review_diff(diff: str) -> str:
    """Review a unified diff and return findings with severity, line numbers and guideline citations."""
    return to_markdown(_agent.review(diff))


@mcp.tool()
def review_pr(repo: str, pr_number: int, post: bool = False) -> str:
    """Review a GitHub pull request (owner/name). Set post=true to publish the review on the PR."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Set GITHUB_TOKEN to review pull requests."
    gh = GitHubClient(token)
    pr = gh.get_pr(repo, pr_number)
    review = _agent.review(gh.get_pr_diff(repo, pr_number), pr.get("title", ""))
    if post:
        gh.post_review(repo, pr_number, review)
    return to_markdown(review)


@mcp.tool()
def search_guidelines(query: str) -> str:
    """Search the team's coding guidelines."""
    hits = _agent.retriever.search(query, k=3)
    return "\n\n".join(f"{h.chunk.label}\n{h.chunk.text}" for h in hits) or "No matching guideline."


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
