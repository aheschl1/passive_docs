import pytest
from passivedocs.diff import parse_diff  # Assuming your function is in a file named 'your_module.py'

def test_apply_simple_diff():
    """Tests a simple replacement of one line and an addition."""
    orig = 'line1\nline2\nline3\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,4 @@
 line1
-line2
+kitty
 line3
+line4
"""
    modified = parse_diff(orig, diff)
    assert modified == 'line1\nkitty\nline3\nline4\n'


def test_apply_deletion_only():
    """Tests a diff that only removes a line."""
    orig = 'a\nb\nc\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,2 @@
 a
-b
 c
"""
    modified = parse_diff(orig, diff)
    assert modified == 'a\nc\n'


def test_error_on_invalid_diff():
    """Ensures a ValueError is raised for an invalid diff hunk header."""
    with pytest.raises(ValueError):
        parse_diff('a\n', '@@ -1,3 +1,4 @@')


def test_multiple_hunks():
    """Tests a diff with two separate hunks."""
    orig = 'one\ntwo\nthree\nfour\nfive\nsix\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,3 @@
 one
-two
+TWO
 three
@@ -4,3 +4,3 @@
 four
-five
+FIVE
 six
"""
    modified = parse_diff(orig, diff)
    assert modified.splitlines() == ['one', 'TWO', 'three', 'four', 'FIVE', 'six']


def test_no_newline_at_eof():
    """Tests handling of the '\\ No newline at end of file' marker."""
    orig = 'a\nb\nc'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,3 @@
 a
 b
-c
\ No newline at end of file
+d
"""
    modified = parse_diff(orig, diff)
    assert modified == 'a\nb\nd\n'


def test_hunk_at_file_boundaries():
    """Tests adding a line at the start and removing one from the end."""
    orig = 'middle\nend\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,2 +1,3 @@
+start
 middle
-end
"""
    modified = parse_diff(orig, diff)
    assert modified.splitlines() == ['start', 'middle']


def test_unapplicable_hunk_raises_error():
    """
    Tests that a diff with a non-matching context raises a ValueError.
    """
    orig = 'a\nb\nc\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,2 @@
 x
-y
 z
"""
    with pytest.raises(ValueError):
        parse_diff(orig, diff)


def test_empty_diff_returns_original():
    """An empty diff should leave the file unchanged."""
    orig = 'a\nb\n'
    diff = ''
    modified = parse_diff(orig, diff)
    assert modified == orig


def test_addition_at_end_with_newline():
    """Adding a line at EOF when original has newline."""
    orig = 'a\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,1 +1,2 @@
 a
+b
"""
    modified = parse_diff(orig, diff)
    assert modified == 'a\nb\n'


def test_preserve_trailing_spaces():
    """Ensure trailing spaces on lines are preserved through replace."""
    orig = 'line \nother\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,2 +1,2 @@
-line 
+LINE 
 other
"""
    modified = parse_diff(orig, diff)
    assert modified == 'LINE \nother\n'


def test_insert_between_lines():
    """Insert a single line between two existing lines."""
    orig = 'a\nc\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,2 +1,3 @@
 a
+b
 c
"""
    modified = parse_diff(orig, diff)
    assert modified == 'a\nb\nc\n'


def test_context_only_hunk_noop():
    """A hunk that only contains context lines should be a no-op."""
    orig = 'one\ntwo\nthree\n'
    diff = """--- a/file.txt
+++ b/file.txt
@@ -1,3 +1,3 @@
 one
 two
 three
"""
    modified = parse_diff(orig, diff)
    assert modified == orig