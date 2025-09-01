import re


def apply_diff(original_content: str, diff_str: str) -> str:
	"""Apply a unified diff string to original_content and return the patched content.

	Supports basic unified-diff hunks with lines starting with ' ', '+', '-', and the
	"\ No newline at end of file" marker. This function does not touch the filesystem.
	"""
	if original_content is None:
		raise ValueError("original_content must be provided")

	orig_lines = original_content.splitlines(keepends=True)
	diff_lines = diff_str.splitlines()
	hunk_re = re.compile(r"^@@ -(?P<o_start>\d+)(?:,(?P<o_count>\d+))? \+(?P<n_start>\d+)(?:,(?P<n_count>\d+))? @@")

	result_lines = []
	orig_idx = 0  # index in orig_lines (0-based)
	i = 0

	while i < len(diff_lines):
		line = diff_lines[i]
		m = hunk_re.match(line)
		if not m:
			# skip headers or metadata
			i += 1
			continue

		o_start = int(m.group('o_start')) - 1

		# copy unchanged lines before hunk
		while orig_idx < o_start and orig_idx < len(orig_lines):
			result_lines.append(orig_lines[orig_idx])
			orig_idx += 1

		# process hunk body
		i += 1
		while i < len(diff_lines) and not diff_lines[i].startswith('@@'):
			dl = diff_lines[i]
			if dl.startswith(' '):
				if orig_idx < len(orig_lines):
					result_lines.append(orig_lines[orig_idx])
					orig_idx += 1
				else:
					result_lines.append(dl[1:] + "\n")
			elif dl.startswith('-'):
				# deletion
				orig_idx += 1
			elif dl.startswith('+'):
				result_lines.append(dl[1:] + "\n")
			elif dl == "\\ No newline at end of file":
				# ignore marker
				pass
			else:
				result_lines.append(dl + "\n")
			i += 1

	# append remaining original lines
	while orig_idx < len(orig_lines):
		result_lines.append(orig_lines[orig_idx])
		orig_idx += 1

	return ''.join(result_lines)
