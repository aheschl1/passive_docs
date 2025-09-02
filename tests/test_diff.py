import pytest
from passivedocs.diff import apply_diff


def test_apply_simple_diff():
    """Tests a simple replacement of one line and an addition."""
    orig = 'line1\nline2\nline3\n'
    diff = r'''
@@ -1,3 +1,4 @@
 line1
-line2
+kitty
 line3
+line4
'''
    modified = apply_diff(orig, diff)
    assert modified == 'line1\nkitty\nline3\nline4\n'


def test_apply_deletion_only():
    """Tests a diff that only removes a line."""
    orig = 'a\nb\nc\n'
    diff = r'''
@@ -1,3 +1,2 @@
 a
-b
 c
'''
    modified = apply_diff(orig, diff)
    assert modified == 'a\nc\n'


def test_error_on_none_content():
    """Ensures a ValueError is raised for None input."""
    with pytest.raises(ValueError):
        apply_diff(None, '')


def test_multiple_hunks():
    """Tests a diff with two separate hunks."""
    orig = 'one\ntwo\nthree\nfour\nfive\nsix\n'
    diff = r'''
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
'''
    modified = apply_diff(orig, diff)
    assert modified.splitlines() == ['one', 'TWO', 'three', 'four', 'FIVE', 'six']


def test_no_newline_at_eof():
    r"""Tests handling of the '\ No newline at end of file' marker."""
    orig = 'a\nb\nc'  # No newline at the end of the original
    diff = r'''
@@ -1,3 +1,3 @@
 a
 b
-c
\ No newline at end of file
+d
'''
    modified = apply_diff(orig, diff)
    assert modified == 'a\nb\nd\n'


def test_hunk_at_file_boundaries():
    """Tests adding a line at the start and removing one from the end."""
    orig = 'middle\nend\n'
    diff = r'''
@@ -1,2 +1,3 @@
+start
 middle
-end
'''
    modified = apply_diff(orig, diff)
    assert modified.splitlines() == ['start', 'middle']


def test_unapplicable_hunk_is_skipped():
    """
    Tests that if a hunk's context cannot be applied, the file is unchanged.
    """
    orig = 'a\nb\nc\n'
    # This diff context 'x', 'y' does not exist in the original.
    diff = r'''
@@ -1,3 +1,2 @@
 x
-y
z
'''
    modified = apply_diff(orig, diff)
    assert modified == orig

def test_empty_diff_returns_original():
    """An empty diff should leave the file unchanged."""
    orig = 'a\nb\n'
    diff = ''
    modified = apply_diff(orig, diff)
    assert modified == orig

def test_addition_at_end_with_newline():
    """Adding a line at EOF when original has newline."""
    orig = 'a\n'
    diff = r'''
@@ -1,1 +1,2 @@
 a
+b
'''
    modified = apply_diff(orig, diff)
    assert modified == 'a\nb\n'

def test_preserve_trailing_spaces():
    """Ensure trailing spaces on lines are preserved through replace."""
    orig = 'line \nother\n'
    diff = r'''
@@ -1,2 +1,2 @@
-line 
+LINE 
 other
'''
    modified = apply_diff(orig, diff)
    assert modified == 'LINE \nother\n'

def test_insert_between_lines():
    """Insert a single line between two existing lines."""
    orig = 'a\nc\n'
    diff = r'''
@@ -1,2 +1,3 @@
 a
+b
 c
'''
    modified = apply_diff(orig, diff)
    assert modified == 'a\nb\nc\n'

def test_context_only_hunk_noop():
    """A hunk that only contains context lines should be a no-op."""
    orig = 'one\ntwo\nthree\n'
    diff = r'''
@@ -1,3 +1,3 @@
 one
 two
 three
'''
    modified = apply_diff(orig, diff)
    assert modified == orig
