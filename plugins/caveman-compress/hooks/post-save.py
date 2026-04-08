#!/usr/bin/env python3
"""
Caveman Compress -- post-save hook (cross-platform).

Automatically re-compresses a file when its .original backup is saved.
Triggered by Claude Code's PostToolUse hook on Write/Edit tool calls.

Claude Code passes the file path via CLAUDE_TOOL_INPUT_FILE_PATH env var.
"""

import os
import re
import subprocess
import sys

ORIGINAL_RE = re.compile(r"^(.+?)\.original(\.[^.]+)?$")

# Resolve plugin root relative to this file: hooks/post-save.py -> plugin root
_HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_ROOT = os.path.dirname(_HOOK_DIR)


def main() -> int:
    file_path = os.environ.get("CLAUDE_TOOL_INPUT_FILE_PATH", "")
    if not file_path:
        return 0

    # Check if the saved file is a .original backup
    basename = os.path.basename(file_path)
    m = ORIGINAL_RE.match(basename)
    if not m:
        return 0

    # Derive compressed file path: CLAUDE.original.md -> CLAUDE.md
    compressed_name = m.group(1) + (m.group(2) or "")
    compressed_path = os.path.join(os.path.dirname(file_path), compressed_name)

    if not os.path.isfile(compressed_path):
        return 0

    print(
        f"[caveman-compress] Re-compressing {compressed_name} "
        f"after edit to {basename}..."
    )

    result = subprocess.run(
        [sys.executable, "-m", "scripts", "compress", compressed_path, "--quiet"],
        cwd=_PLUGIN_ROOT,
    )

    if result.returncode == 0:
        print("[caveman-compress] Done.")
    else:
        print("[caveman-compress] Compression failed.", file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
