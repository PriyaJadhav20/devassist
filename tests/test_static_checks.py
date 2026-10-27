from devassist.diff_parser import parse_diff
from devassist.heuristic import heuristic_review
from evals.dataset import CASES, _diff


def rules(diff):
    return {c.rule for c in heuristic_review(diff).comments}


def test_flags_core_issues():
    for case in CASES:
        assert rules(case["diff"]) == set(case["expected"]), case["name"]


def test_debug_print_ignored_in_tests():
    assert "debug-output" not in rules(_diff("tests/test_x.py", ["print('x')"]))
    assert "debug-output" in rules(_diff("app/x.py", ["print('x')"]))


def test_comments_carry_guideline_citation():
    review = heuristic_review(_diff("a.py", ["eval(x)"]))
    assert review.comments[0].guideline.startswith("security.md")
    assert review.verdict == "changes_requested"


def test_comment_cap_and_valid_lines():
    diff = _diff("a.py", ["x == None"] * 30)
    review = heuristic_review(diff)
    visible = parse_diff(diff)[0].visible
    assert len(review.comments) == 10 and all(c.line in visible for c in review.comments)
