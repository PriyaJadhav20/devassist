"""Deterministic checks. They back the offline mode and feed the LLM agent as a tool."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .diff_parser import FileDiff
from .schemas import ReviewComment, Severity


@dataclass(frozen=True)
class Rule:
    id: str
    severity: Severity
    pattern: re.Pattern[str]
    message: str
    query: str
    skip_tests: bool = False


def _r(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


RULES: list[Rule] = [
    Rule("hardcoded-secret", "security",
         _r(r"""(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*["'][^"']{8,}["']|AKIA[0-9A-Z]{16}"""),
         "Possible hardcoded credential. Load it from an environment variable or a secret manager.",
         "secrets credentials environment variables"),
    Rule("sql-injection", "security",
         _r(r"""\.(execute|executemany|query|raw)\(\s*(f["']|["'][^"']*["']\s*(%|\+|\.format))"""),
         "SQL is built with string formatting. Use parameterized queries to prevent injection.",
         "sql injection parameterized queries"),
    Rule("eval-exec", "security", _r(r"\b(eval|exec)\s*\("),
         "eval/exec runs arbitrary code. Parse the input explicitly instead.",
         "eval exec arbitrary code"),
    Rule("shell-injection", "security", _r(r"shell\s*=\s*True|\bos\.system\s*\("),
         "Shell execution with dynamic input risks command injection. Pass an argument list instead.",
         "shell command injection subprocess"),
    Rule("weak-hash", "security", _r(r"hashlib\.(md5|sha1)\s*\("),
         "MD5/SHA-1 are broken for security use. Use SHA-256 or a password hasher such as bcrypt or argon2.",
         "hashing passwords weak hash"),
    Rule("tls-verify-off", "security", _r(r"verify\s*=\s*False"),
         "TLS verification is disabled. Fix the certificate instead of turning verification off.",
         "tls certificate verification"),
    Rule("unsafe-deserialize", "security", _r(r"pickle\.loads?\(|yaml\.load\((?!.*Loader)"),
         "Unsafe deserialization can execute code. Use json or yaml.safe_load.",
         "unsafe deserialization pickle yaml"),
    Rule("xss-innerhtml", "security", _r(r"\.innerHTML\s*\+?="),
         "Assigning innerHTML with dynamic data enables XSS. Use textContent or sanitize the input.",
         "xss innerhtml sanitize"),
    Rule("bare-except", "bug", _r(r"^\s*except\s*:"),
         "Bare except hides real errors and catches KeyboardInterrupt. Catch specific exceptions.",
         "exceptions swallow bare except error handling"),
    Rule("mutable-default", "bug", _r(r"def\s+\w+\(.*=\s*(\[\]|\{\}|set\(\))"),
         "Mutable default arguments are shared between calls. Default to None and create the value inside.",
         "mutable default arguments"),
    Rule("none-compare", "style", _r(r"[=!]=\s*None\b"),
         "Compare to None with `is` / `is not`.", "python style comparisons none"),
    Rule("debug-output", "style", _r(r"^\s*(print\(|console\.log\(|debugger\b)"),
         "Remove debug output or use the logging module.", "logging debug print statements", True),
    Rule("todo-marker", "suggestion", _r(r"\b(TODO|FIXME|HACK)\b"),
         "Track this in an issue instead of leaving a marker in the code.",
         "todo comments issues tracking"),
]


def _is_test(path: str) -> bool:
    low = path.lower()
    return "test" in low.split("/")[-1] or "/tests/" in f"/{low}"


def run_static_checks(files: list[FileDiff]) -> list[ReviewComment]:
    found: list[ReviewComment] = []
    seen: set[tuple[str, int, str]] = set()
    for f in files:
        for line_no, text in f.added.items():
            for rule in RULES:
                if rule.skip_tests and _is_test(f.path):
                    continue
                key = (f.path, line_no, rule.id)
                if key in seen or not rule.pattern.search(text):
                    continue
                seen.add(key)
                found.append(ReviewComment(file=f.path, line=line_no, severity=rule.severity,
                                           comment=rule.message, rule=rule.id))
    return found
