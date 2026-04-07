---
name: caveman-diff
description: Show a paragraph-level diff between the original and compressed version of a file
allowed-tools: Bash
---

Show the diff for the file provided by the user.

Run:
```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python -m scripts diff $ARGUMENTS
```

Display the diff output to the user.
