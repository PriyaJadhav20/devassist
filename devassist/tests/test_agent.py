from types import SimpleNamespace as NS

from devassist.agent import Agent
from evals.dataset import _diff

DIFF = _diff("a.py", ["import os", "x = eval(input())"])


def tool_use(name, args, id="t1"):
    return NS(content=[NS(type="tool_use", name=name, input=args, id=id)], stop_reason="tool_use")


class Fake:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), 0
        self.messages = self

    def create(self, **kwargs):
        self.calls += 1
        return self.responses.pop(0)


def test_agent_runs_tools_then_submits_and_drops_bad_lines():
    submit = {"summary": "One real issue.", "comments": [
        {"file": "a.py", "line": 2, "severity": "security", "comment": "eval on input"},
        {"file": "a.py", "line": 99, "severity": "bug", "comment": "hallucinated line"},
        {"file": "nope.py", "line": 1, "severity": "bug", "comment": "unknown file"}]}
    fake = Fake([tool_use("list_changed_files", {}), tool_use("search_guidelines", {"query": "eval"}),
                 tool_use("submit_review", submit)])
    review = Agent(client=fake).review(DIFF)
    assert review.mode == "llm" and fake.calls == 3
    assert [(c.file, c.line) for c in review.comments] == [("a.py", 2)]


def test_agent_falls_back_when_llm_fails():
    class Boom:
        messages = None

        def __init__(self):
            self.messages = self

        def create(self, **kw):
            raise TimeoutError("down")

    review = Agent(client=Boom()).review(DIFF)
    assert review.comments and "LLM unavailable" in review.summary


def test_agent_stops_after_max_steps():
    fake = Fake([tool_use("list_changed_files", {}) for _ in range(5)])
    review = Agent(client=fake, max_steps=3).review(DIFF)
    assert fake.calls == 3 and review.comments


def test_offline_mode_and_empty_diff(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = Agent()
    assert agent.mode == "heuristic" and agent.review(DIFF).comments
    assert agent.review("  ").comments == []
