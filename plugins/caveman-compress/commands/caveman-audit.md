---
name: caveman-audit
description: Scan for compressible files and show savings estimates without writing any changes
allowed-tools: Bash
---

Audit the directory provided by the user (default: current directory).

Run:
```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python -m scripts audit $ARGUMENTS
```

Show the audit table. No files are modified.
