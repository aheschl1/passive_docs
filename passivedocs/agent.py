import json
import logging
import os
from typing import Any, Dict, List, Optional

import dotenv
import ollama

from .diff import apply_diff


logger = logging.getLogger(__name__)


TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "diff",
            "description": "Return a unified diff hunk for the current file by providing the hunk header and the hunk body separately. 'header' should contain the '@@ -old_start,old_count +new_start,new_count @@' line and 'diff' should contain the hunk body (context, removals, additions) without the header.",
            "parameters": {
                "type": "object",
                "properties": {
                    "header": {"type": "string", "description": "Unified diff hunk header, e.g. '@@ -42,3 +42,5 @@'"},
                    "diff": {"type": "string", "description": "Hunk body: context, additions, deletions (without the header)"},
                },
                "required": ["header", "diff"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view",
            "description": "Request another file by repository-relative path",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path to the file to view"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "next",
            "description": "Indicate that no change is required",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


class DocAgent:
    """Agent that drives the documentation assistant.

    Responsibilities are split into small helper methods for readability and easier testing.
    """

    def __init__(
        self,
        readme: str,
        files: List[str],
        client: Optional[ollama.Client] = None,
        process_all: bool = False,
    ) -> None:
        dotenv.load_dotenv()
        self.client = client or ollama.Client(host=os.environ.get("ENDPOINT"))
        self.files = files
        self.readme = readme
        self.process_all = process_all
        self.system_prompt = self._build_system_prompt()

    # --- file I/O helpers -----------------------------------------------------------------
    def _read_file(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _handle_file_update(self, path: str, diff: str) -> None:
        """Apply a unified diff to a file on disk."""
        logger.info("Applying diff to %s", path)
        logger.info("Diff:\n%s", diff)
        original = self._read_file(path)
        updated = apply_diff(original, diff)
        self._write_file(path, updated)
        logger.info(
            "Updated file %s (%d -> %d bytes)",
            path,
            len(original.encode("utf-8")),
            len(updated.encode("utf-8")),
        )

    # --- prompt/messages builders -----------------------------------------------------------
    def _build_system_prompt(self) -> str:
        files_list = "\n".join(self.files)
        prompt = (
            "You are a documentation assistant. Add documentation comments to code and update README/docs without changing program behavior. You will receive one file at a time with line numbers for reference only. Always respond with exactly one tool call.\n\n"
            "Repository files:\n"
            "{files}\n\n"
            "Repository readme:\n"
            "{readme}\n\n"
            "You must only respond using the provided tools and follow the unified diff format rules below. If you cannot produce documentation based on current context, use `view(path=...)` to request more context, or call `next()` to skip the file.\n\n"
            "TOOLS:\n"
            "  - `view(path: str)` - Request content of another file for context\n"
            "  - `diff(header: str, diff: str)` - Apply changes via a single unified diff hunk\n"
            "  - header must be EXACTLY the hunk header, e.g. '@@ -42,3 +42,5 @@' (no surrounding text)\n"
            "  - diff must contain only the hunk body (no header). Every body line MUST begin with one of: space (' '), '-' or '+'\n"
            "  - `next()` - No changes needed for current file\n\n"
            "DIFF RULES (STRICT):\n"
            "- Every line in the hunk body must start with a single prefix character: ' ' (context), '-' (deletion), or '+' (addition).\n"
            "- Empty original lines are represented by a '-' line with no following space (i.e. '-' then newline), not '- '.\n"
            "- The header counts MUST MATCH the body: old_count = number of lines in the body that start with ' ' or '-', new_count = number of lines that start with ' ' or '+'.\n"
            "- Include 1-3 context lines (prefixed with a space) around edits to ensure deterministic matching. Context lines must match the file EXACTLY, including leading/trailing whitespace and newlines.\n"
            "- Added lines ('+') should include the exact characters you want inserted and should end with a newline in the real file.\n"
            "- If the file ends without a trailing newline, use a literal line '\\ No newline at end of file' on its own line in the body where appropriate.\n"
            "- Do NOT include line-number prefixes in the diff body; use the raw content.\n"
            "- Always validate mentally that the header counts equal the body composition before returning. If unsure, request `view()` for the file and nearby context.\n\n"
            "QUICK EXAMPLES (invalid -> valid):\n"
            "Invalid (missing context prefix, wrong counts):\n"
            "@@ -85,1 +85,5 @@\n"
            "Serialization works only for 64-bit targets but is endian-agnostic. Big-endian machines may serialize less efficiently due to byte swaps for some fixed-size primitives.\n"
            "Valid corrected form (header and body must match counts and prefixes):\n"
            "@@ -85,1 +85,5 @@\n"
            " Serialization works only for 64-bit targets but is endian-agnostic. Big-endian machines may serialize less efficiently due to byte swaps for some fixed-size primitives.\n"
            "+## Building\n"
            "+\n"
            "+```bash\n"
            "+cargo build\n"
            "+```\n\n"
            "WORKFLOW:\n"
            "- Present only one small hunk per `diff()` call. Keep changes minimal.\n"
            "- If you produce a `diff()` tool call, ensure the header and body are consistent and that every body line uses the correct prefix.\n"
            "- If you are unable to produce a valid hunk, call `view()` or `next()`.\n\n"
            "Be strict: malformed hunks (wrong prefixes, mismatched counts, or stray text) will be rejected."
        )
        return prompt.format(files=files_list, readme=self.readme)

    def _build_initial_messages(self, path: str) -> List[ollama.Message]:
        content = self._read_file(path)
        # Present the file to the model with explicit one-based line numbers
        # prefixed for each line. Keep original line endings.
        numbered_lines: List[str] = []
        for idx, ln in enumerate(content.splitlines(keepends=True), start=1):
            # prefix like '  1: ' for readability
            numbered_lines.append(f"{idx}: {ln}")
        numbered_content = "".join(numbered_lines)

        return [
            ollama.Message(role="system", content=self.system_prompt),
            ollama.Message(role="user", content=f"Document {path}. The following is the content (lines are prefixed with their line numbers for reference):"),
            ollama.Message(role="user", content=numbered_content),
        ]

    # --- tool call processing --------------------------------------------------------------
    def _process_tool_call(self, 
                           file: str, 
                           tool_call: Any,
                           agent_message: ollama.Message,
                           messages: List[ollama.Message]
                        ) -> Optional[bool]:
        """Handle a single tool call from the model. Returns True if conversation should end."""
        function_name = tool_call.function.name
        # arguments may be a raw string depending on the client; attempt to parse
        raw_args = tool_call.function.arguments
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except Exception:
            args = raw_args

        logger.info(" - Tool: %s", function_name)

        if function_name == "diff":
            # Combine the provided header and diff body into a single unified diff string
            header = args.get("header").strip()
            body = args.get("diff").lstrip('\n')
            if header is None or body is None:
                logger.error("Diff tool call missing 'header' or 'diff' fields: %s", args)
                messages.append(agent_message)
                messages.append(ollama.Message(role="tool", content="Error: 'header' and 'diff' are required for diff tool.", tool_name="diff"))
                return False
            full_diff = f"{header}\n{body}"
            self._handle_file_update(file, full_diff)
            logger.info("Applied diff tool call for %s", file)
            messages.append(agent_message)
            messages.append(
                ollama.Message(role="tool", content=f"Applied diff to {file}.", tool_name="diff")
            )
            updated = self._read_file(file)
            # add line nums
            numbered_lines: List[str] = []
            for idx, ln in enumerate(updated.splitlines(keepends=True), start=1):
                # prefix like '  1: ' for readability
                numbered_lines.append(f"{idx}: {ln}")
            updated = "".join(numbered_lines)
            messages.append(ollama.Message(role="user", content=f"Continue documenting if necessary, or move on if not. Here's the new content: {updated}"))
            return False

        if function_name == "view":
            messages.append(agent_message)
            try:
                logger.info("Reading file %s", args["path"])
                other = self._read_file(args["path"])
            except Exception as e:
                logger.error("Error reading file %s: %s", args["path"], e)
                other = "Error reading file. Path does not exit. Try again, or move on."
            messages.append(ollama.Message(role="tool", content=other, tool_name="view"))
            return False

        if function_name == "next":
            return True

        # Unknown tool - ignore but log
        logger.warning("Unknown tool call: %s", function_name)
        return False

    # --- main loop ------------------------------------------------------------------------
    def iterate(self) -> None:
        """Iterate over files. By default matches original behavior of processing only the first file.

        To process all files, instantiate DocAgent(..., process_all=True).
        """
        for file in self.files:
            logger.info("Processing file: %s", file)
            self._handle_single_file(file)

    def _handle_single_file(self, file: str) -> None:
        messages = self._build_initial_messages(file)
        done = False
        while not done:
            try:
                response: ollama.ChatResponse = self.client.chat(
                    model=os.environ.get("MODEL"), messages=messages, tools=TOOLS, stream=False,
                    keep_alive="20m"
                )
            except Exception as e:
                logger.error("Error occurred while calling chat API: %s", e)
                continue

            if not (hasattr(response.message, "tool_calls") and response.message.tool_calls):
                # nothing to do; end conversation for this file
                break

            for tool_call in response.message.tool_calls:
                agent_message = response.message
                try:
                    should_end = self._process_tool_call(file, tool_call, agent_message, messages)
                except Exception as e:
                    logger.error("Error processing tool call for %s: %s", file, e)
                    should_end = False
                if should_end:
                    done = True
                    break
