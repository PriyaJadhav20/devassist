from devassist.diff_parser import parse_diff

DIFF = """diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,3 +10,4 @@
 keep
-old
+new
+newer
 tail
diff --git a/gone.py b/gone.py
--- a/gone.py
+++ /dev/null
@@ -1 +0,0 @@
-bye
"""


def test_line_numbers_and_visibility():
    files = parse_diff(DIFF)
    assert [f.path for f in files] == ["a.py"]
    f = files[0]
    assert f.added == {11: "new", 12: "newer"}
    assert f.visible == {10, 11, 12, 13}


def test_empty_diff():
    assert parse_diff("") == []
