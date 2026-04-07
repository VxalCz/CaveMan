#!/usr/bin/env bash
# Caveman Compress — post-save hook
#
# Automatically re-compresses a file when its .original backup is saved.
# Triggered by Claude Code's PostToolUse hook on Write/Edit tool calls.
#
# Claude Code passes the tool input as JSON via CLAUDE_TOOL_INPUT env var.
# We extract the file_path and check if it's a .original.* file.

set -euo pipefail

# Extract file_path from the tool input JSON
FILE_PATH="${CLAUDE_TOOL_INPUT_FILE_PATH:-}"

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Check if the saved file is a .original backup
if [[ ! "$FILE_PATH" =~ \.original\.[^.]+$ ]] && [[ ! "$FILE_PATH" =~ \.original$ ]]; then
    exit 0
fi

# Derive the compressed file path by removing .original
COMPRESSED="${FILE_PATH/.original./\.}"
COMPRESSED="${COMPRESSED%.original}"

# Remove the escaped dot we introduced above (simple approach)
# More robust: strip the literal ".original" segment
COMPRESSED=$(python3 -c "
import re, sys
p = sys.argv[1]
# e.g. CLAUDE.original.md -> CLAUDE.md
#      README.original     -> README
m = re.match(r'^(.+?)\.original(\.[^.]+)?$', p)
if m:
    print(m.group(1) + (m.group(2) or ''))
else:
    print(p)
" "$FILE_PATH")

if [[ ! -f "$COMPRESSED" ]]; then
    exit 0
fi

echo "[caveman-compress] Re-compressing $COMPRESSED after edit to $(basename "$FILE_PATH")…"

python -m plugin.caveman_compress.scripts compress "$COMPRESSED" --quiet

echo "[caveman-compress] Done."
