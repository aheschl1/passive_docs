def parse_diff(original_text, unified_diff):
    r"""Apply a unified diff to original_text and return the patched text.

    This implementation supports multiple hunks, context/add/delete lines,
    and the "\ No newline at end of file" marker used in unified diffs.

    Raises ValueError when the diff can't be applied cleanly.
    """
    if not unified_diff:
        return original_text

    original_lines = original_text.splitlines()
    # Keep track if original had a trailing newline
    original_ends_with_nl = original_text.endswith('\n')

    diff_lines = unified_diff.splitlines()

    out_lines = []
    src_index = 0  # 0-based index into original_lines

    i = 0
    # Find first hunk and ensure file headers exist before it
    first_hunk_idx = None
    for idx, line in enumerate(diff_lines):
        if line.startswith('@@'):
            first_hunk_idx = idx
            break
    if first_hunk_idx is None:
        # no hunks -> return original
        return original_text
    # Allow diffs that start immediately with hunks (no '---'/'+++' headers)
    i = first_hunk_idx

    # global flag whether the new file ends without newline
    new_file_no_nl = False

    while i < len(diff_lines):
        header = diff_lines[i]
        if not header.startswith('@@'):
            # any trailing metadata is ignored
            i += 1
            continue

        # Parse hunk header like: @@ -l,s +l2,s2 @@
        parts = header.split()
        if len(parts) < 3:
            raise ValueError('Invalid unified diff hunk header.')

        # Ensure hunk has at least one body line following the header
        if i + 1 >= len(diff_lines) or diff_lines[i + 1].startswith('@@'):
            raise ValueError('Hunk header not followed by hunk body.')

        try:
            orig_range = parts[1]
            # orig_range is like -start[,len]
            if not orig_range.startswith('-'):
                raise ValueError('Invalid unified diff hunk header.')
            a = orig_range[1:]
            if ',' in a:
                a_start_str, a_len_str = a.split(',', 1)
                a_start = int(a_start_str)
                a_len = int(a_len_str)
            else:
                a_start = int(a)
                a_len = 1
        except Exception:
            raise ValueError('Invalid unified diff hunk header.')

        # Fill in untouched lines up to the hunk's start (a_start is 1-based)
        target_index = a_start - 1
        if src_index > target_index:
            # overlapping hunks or invalid positions
            raise ValueError('Hunk overlaps previous hunk or is out of order.')
        out_lines.extend(original_lines[src_index:target_index])
        src_index = target_index

        # Process hunk body
        i += 1
        last_sign = None
        while i < len(diff_lines):
            dl = diff_lines[i]
            if dl.startswith('@@'):
                break
            if dl == "\\ No newline at end of file":
                # Marker applies to the previous diff line. If that line was an addition,
                # then the new file's last line has no trailing newline.
                if last_sign == '+':
                    new_file_no_nl = True
                i += 1
                continue

            if not dl:
                # empty line in diff represents a context/add/delete line with empty content
                # but unified diffs prepend a space/+/- so an empty string here is unexpected
                raise ValueError('Invalid diff line format: empty line')

            sign = dl[0]
            content = dl[1:]
            if sign == ' ':
                # context: must match original
                if src_index >= len(original_lines) or original_lines[src_index] != content:
                    raise ValueError('Context line mismatch when applying hunk.')
                out_lines.append(content)
                src_index += 1
                last_sign = ' '
            elif sign == '-':
                # deletion: original must match, but do not append
                if src_index >= len(original_lines) or original_lines[src_index] != content:
                    raise ValueError('Deletion line mismatch when applying hunk.')
                src_index += 1
                last_sign = '-'
            elif sign == '+':
                # addition: add to output, do not advance src_index
                out_lines.append(content)
                last_sign = '+'
            else:
                raise ValueError('Invalid diff line format.')

            i += 1

    # Append any remaining original lines
    out_lines.extend(original_lines[src_index:])

    # Determine final newline: if the diff removed the final newline marker or
    # the original ended with newline and no explicit removal was indicated, end with \n.
    # Heuristic: if unified_diff contains the marker "\\ No newline at end of file" for the
    # new file (a + line) we should ensure trailing newline is absent. Tests expect a trailing newline
    # in most cases; we will use this rule: if the last line of the diff body for additions was
    # followed by the No newline marker (i.e., the marker appeared anywhere), then we consider no trailing nl.

    new_text = '\n'.join(out_lines)

    # Final newline handling:
    # If any hunk had an explicit marker that the new file has no trailing newline
    # we should remove the final newline. Otherwise, ensure the file ends with a newline
    # if the original ended with one or if the diff appears to add/replace the final line.
    if new_file_no_nl:
        # Remove final newline if present
        if new_text.endswith('\n'):
            new_text = new_text[:-1]
    else:
        if original_ends_with_nl or (original_lines and not new_text.endswith('\n')):
            if not new_text.endswith('\n'):
                new_text = new_text + '\n'

    return new_text


# Backwards compatible name expected by the package-level API
def apply_diff(original_text, unified_diff):
    """Backward-compatible wrapper around parse_diff."""
    return parse_diff(original_text, unified_diff)
