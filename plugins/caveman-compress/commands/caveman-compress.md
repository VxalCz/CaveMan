---
name: caveman-compress
description: Compress a markdown/text file (or directory) to save input tokens on future sessions
allowed-tools: Bash
---

Compress the file or directory provided by the user.

Supported flags:
- `--model <MODEL>` / `-m` — Claude model for compression (e.g. claude-haiku-4-5-20251001 for cheaper runs)
- `--dry-run` / `-n` — print compressed output to stdout without writing files
- `--min-savings <PCT>` / `-s` — skip files with estimated savings below PCT% (default: 20)
- `--quiet` / `-q` — suppress progress output

Run:
```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python -m scripts compress $ARGUMENTS
```

Report the result: tokens before/after, savings %, any warnings.
