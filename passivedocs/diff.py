import re
from typing import Optional


class Hunk:
    def __init__(self, old_start: int, old_count: int, new_start: int, new_count: int, body: list[str]):
        self.old_start = old_start
        self.old_count = old_count
        self.new_start = new_start
        self.new_count = new_count
        self.body = body

    def original_seq(self) -> list[str]:
        """Return the lines (without +/-) that must exist in the original file."""
        return [ln[1:] for ln in self.body if ln.startswith(" ") or ln.startswith("-")]


def parse_diff(diff_str: str) -> list[Hunk]:
    """Turn a unified diff string into structured hunks."""
    hunk_re = re.compile(
        r"^@@ -(?P<o_start>\d+)(?:,(?P<o_count>\d+))? "
        r"\+(?P<n_start>\d+)(?:,(?P<n_count>\d+))? @@"
    )

    hunks: list[Hunk] = []
    lines = diff_str.splitlines()
    i = 0

    while i < len(lines):
        m = hunk_re.match(lines[i])
        if not m:
            i += 1
            continue

        old_start = int(m.group("o_start"))
        old_count = int(m.group("o_count") or 1)
        new_start = int(m.group("n_start"))
        new_count = int(m.group("n_count") or 1)

        i += 1
        body: list[str] = []
        while i < len(lines) and not hunk_re.match(lines[i]):
            body.append(lines[i])
            i += 1

        hunks.append(Hunk(old_start, old_count, new_start, new_count, body))

    return hunks


def apply_hunk(orig_lines: list[str], hunk: Hunk) -> list[str]:
    """Apply a single hunk to orig_lines using exact line numbers."""
    # Line numbers in unified diff are 1-based
    pos = hunk.old_start - 1
    result: list[str] = []

    # Verify that the hunk's original context matches the file at the
    # expected position. If it doesn't, skip applying this hunk and
    # return the original lines unchanged.
    expected = hunk.original_seq()
    # slice of original lines that the hunk is supposed to replace/consume
    orig_slice = orig_lines[pos: pos + hunk.old_count]
    # normalize by stripping a single trailing newline for comparison
    orig_slice_norm = [ln.rstrip("\n") for ln in orig_slice]
    if orig_slice_norm != expected:
        # Hunk cannot be applied; leave file unchanged
        return orig_lines

    # Copy everything before the hunk
    result.extend(orig_lines[:pos])

    # Apply the hunk body
    consume_idx = pos
    for line in hunk.body:
        if line.startswith(" "):  # context
            result.append(orig_lines[consume_idx])
            consume_idx += 1
        elif line.startswith("-"):  # deletion
            consume_idx += 1
        elif line.startswith("+"):  # addition
            result.append(line[1:] + "\n")
        elif line == r"\ No newline at end of file":
            pass
        else:
            raise ValueError(f"Unexpected diff line: {line}")

    # Copy the rest of the original file
    result.extend(orig_lines[consume_idx:])
    return result


def apply_diff(original_content: str, diff_str: str) -> str:
    """Apply all hunks to original_content using line numbers only."""
    if original_content is None:
        raise ValueError("original_content must not be None")
    orig_lines = original_content.splitlines(keepends=True)
    hunks = parse_diff(diff_str)

    for hunk in hunks:
        orig_lines = apply_hunk(orig_lines, hunk)

    return "".join(orig_lines)
