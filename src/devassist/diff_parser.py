"""Parse unified diffs so review comments can be validated against real lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass
class FileDiff:
    path: str
    added: dict[int, str] = field(default_factory=dict)  # new line number -> text
    visible: set[int] = field(default_factory=set)  # lines GitHub can attach comments to
    patch: list[str] = field(default_factory=list)


def parse_diff(diff: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    current: FileDiff | None = None
    new_line = 0
    in_hunk = False
    for raw in diff.splitlines():
        if raw.startswith("diff --git"):
            current, in_hunk = None, False
            continue
        if raw.startswith("+++ ") and not in_hunk:
            target = raw[4:].strip()
            if target == "/dev/null":
                current = None
            else:
                current = FileDiff(path=target[2:] if target.startswith("b/") else target)
                files.append(current)
            continue
        if raw.startswith("--- ") and not in_hunk:
            continue
        match = HUNK.match(raw)
        if match and current is not None:
            new_line, in_hunk = int(match.group(1)), True
            current.patch.append(raw)
            continue
        if current is None or not in_hunk:
            continue
        if raw.startswith("+"):
            current.added[new_line] = raw[1:]
            current.visible.add(new_line)
            current.patch.append(raw)
            new_line += 1
        elif raw.startswith("-"):
            current.patch.append(raw)
        elif raw.startswith("\\"):
            continue
        else:
            current.visible.add(new_line)
            current.patch.append(raw)
            new_line += 1
    return files
