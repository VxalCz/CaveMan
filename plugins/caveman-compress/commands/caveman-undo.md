---
name: caveman-undo
description: Restore a compressed file from its .original backup
allowed-tools: Bash
---

Restore the file provided by the user from its `.original` backup.

Run:
```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python -m scripts undo $ARGUMENTS
```

Confirm the file was restored successfully.
