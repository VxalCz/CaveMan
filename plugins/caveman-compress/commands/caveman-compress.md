---
name: caveman-compress
description: Compress a markdown/text file (or directory) to save input tokens on future sessions
allowed-tools: Bash
---

Compress the file or directory provided by the user.

Run:
```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python -m scripts compress $ARGUMENTS
```

Report the result: tokens before/after, savings %, any warnings.
