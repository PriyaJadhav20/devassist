from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["security", "bug", "suggestion", "style"]
SEVERITY_ORDER = {"security": 0, "bug": 1, "suggestion": 2, "style": 3}


class ReviewComment(BaseModel):
    file: str
    line: int = Field(ge=1)
    severity: Severity
    comment: str
    rule: Optional[str] = None
    guideline: Optional[str] = None


class Review(BaseModel):
    summary: str
    comments: list[ReviewComment] = Field(default_factory=list)
    mode: str = "heuristic"

    @property
    def verdict(self) -> str:
        if any(c.severity in ("security", "bug") for c in self.comments):
            return "changes_requested"
        return "comments" if self.comments else "looks_good"
