"""Labelled PRs: each case lists the rule ids a good reviewer must catch."""


def _diff(path: str, lines: list[str]) -> str:
    body = "\n".join("+" + line for line in lines)
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,{len(lines)} @@\n{body}\n"


CASES = [
    {"name": "hardcoded key", "expected": ["hardcoded-secret"],
     "diff": _diff("svc/client.py", ['API_KEY = "sk_live_9f8e7d6c5b4a"', "def call():", "    return API_KEY"])},
    {"name": "sql injection", "expected": ["sql-injection"],
     "diff": _diff("svc/db.py", ["def find(db, name):", "    return db.execute(f\"SELECT * FROM t WHERE n = '{name}'\")"])},
    {"name": "eval of input", "expected": ["eval-exec"],
     "diff": _diff("svc/calc.py", ["def calc(expr):", "    return eval(expr)"])},
    {"name": "shell injection", "expected": ["shell-injection"],
     "diff": _diff("svc/run.py", ["import subprocess", "def run(cmd):", "    subprocess.call(cmd, shell=True)"])},
    {"name": "weak hash", "expected": ["weak-hash"],
     "diff": _diff("svc/pw.py", ["import hashlib", "def h(p):", "    return hashlib.md5(p.encode()).hexdigest()"])},
    {"name": "tls off", "expected": ["tls-verify-off"],
     "diff": _diff("svc/http.py", ["import requests", "def get(u):", "    return requests.get(u, verify=False)"])},
    {"name": "swallowed errors", "expected": ["bare-except"],
     "diff": _diff("svc/io.py", ["def read(p):", "    try:", "        return open(p).read()", "    except:", "        return ''"])},
    {"name": "mutable default", "expected": ["mutable-default"],
     "diff": _diff("svc/cache.py", ["def add(item, bucket=[]):", "    bucket.append(item)", "    return bucket"])},
    {"name": "xss", "expected": ["xss-innerhtml"],
     "diff": _diff("web/ui.js", ["function show(el, v) {", "  el.innerHTML = v;", "}"])},
    {"name": "clean change", "expected": [],
     "diff": _diff("svc/math_utils.py", ["def clamp(v: int, lo: int, hi: int) -> int:", "    return max(lo, min(v, hi))"])},
]
