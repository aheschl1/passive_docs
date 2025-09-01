import pathlib
import importlib.util
import pytest


def load_diff_module():
    spec = importlib.util.spec_from_file_location(
        "diff_mod",
        str(pathlib.Path(__file__).resolve().parents[1] / "src" / "diff.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_apply_simple_diff(tmp_path):
    p = tmp_path / "orig.txt"
    p.write_text('line1\nline2\nline3\n')

    diff = '''--- a/orig.txt
+++ b/orig.txt
@@ -1,3 +1,4 @@
 line1
-line2
+kitty
 line3
+line4
'''

    mod = load_diff_module()
    apply_diff = mod.apply_diff

    orig = p.read_text()
    modified = apply_diff(orig, diff)

    assert modified == 'line1\nkitty\nline3\nline4\n'

    p.write_text(modified)
    assert p.read_text() == 'line1\nkitty\nline3\nline4\n'


def test_apply_deletion_only(tmp_path):
    p = tmp_path / "orig2.txt"
    p.write_text('a\nb\nc\n')

    diff = '''--- a/orig2.txt
+++ b/orig2.txt
@@ -1,3 +1,2 @@
 a
-b
 c
'''

    mod = load_diff_module()
    apply_diff = mod.apply_diff

    orig = p.read_text()
    modified = apply_diff(orig, diff)

    assert modified == 'a\nc\n'
    p.write_text(modified)
    assert p.read_text() == 'a\nc\n'


def test_errors_when_not_loaded(tmp_path):
    p = tmp_path / "orig3.txt"
    p.write_text('x\ny\n')
    diff = ''

    mod = load_diff_module()
    apply_diff = mod.apply_diff

    with pytest.raises(ValueError):
        apply_diff(None, diff)


def test_multiple_hunks(tmp_path):
    p = tmp_path / "multi.txt"
    p.write_text('one\ntwo\nthree\nfour\nfive\nsix\n')

    diff = '''--- a/multi.txt
+++ b/multi.txt
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

    mod = load_diff_module()
    apply_diff = mod.apply_diff

    orig = p.read_text()
    modified = apply_diff(orig, diff)

    assert 'TWO' in modified
    assert 'FIVE' in modified
    p.write_text(modified)
    assert p.read_text().splitlines() == ['one', 'TWO', 'three', 'four', 'FIVE', 'six']


def test_no_newline_at_eof(tmp_path):
    p = tmp_path / "nonewline.txt"
    # write without trailing newline
    p.write_text('a\nb\nc')

    diff = '''--- a/nonewline.txt
+++ b/nonewline.txt
@@ -1,3 +1,3 @@
 a
 b
-c
\ No newline at end of file
+d
'''

    mod = load_diff_module()
    apply_diff = mod.apply_diff

    orig = p.read_text()
    modified = apply_diff(orig, diff)

    # parser will add newline for additions
    assert modified == 'a\nb\nd\n'
    p.write_text(modified)
    assert p.read_text() == 'a\nb\nd\n'


def test_hunk_at_file_boundaries(tmp_path):
    p = tmp_path / "bounds.txt"
    p.write_text('middle\nend\n')

    diff = '''--- a/bounds.txt
+++ b/bounds.txt
@@ -1,2 +1,3 @@
+start
 middle
-end
'''

    mod = load_diff_module()
    apply_diff = mod.apply_diff

    orig = p.read_text()
    modified = apply_diff(orig, diff)

    assert modified.splitlines() == ['start', 'middle']
    p.write_text(modified)
    assert p.read_text().splitlines() == ['start', 'middle']
