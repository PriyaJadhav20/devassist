from __future__ import annotations

from .schemas import SEVERITY_ORDER, Review, ReviewComment

ICONS = {"security": "🔒 Security", "bug": "🐛 Bug", "suggestion": "💡 Suggestion", "style": "🎨 Style"}


def format_comment(c: ReviewComment) -> str:
    text = f"**{ICONS[c.severity]}**: {c.comment}"
    if c.guideline:
        text += f"\n\n_Guideline: {c.guideline}_"
    return text


def to_markdown(review: Review) -> str:
    lines = [f"### DevAssist review ({review.verdict.replace('_', ' ')})", "", review.summary, ""]
    for c in sorted(review.comments, key=lambda c: (SEVERITY_ORDER[c.severity], c.file, c.line)):
        lines.append(f"- `{c.file}:{c.line}` {format_comment(c)}")
    return "\n".join(lines)
