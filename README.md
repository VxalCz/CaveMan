# Caveman

Claude Code plugin that cuts token usage on both sides of the conversation.

| Component | What it does | Where it saves | Savings |
|-----------|-------------|----------------|---------|
| **Caveman mode** | Forces Claude to respond concisely | Output tokens (responses) | ~65% |
| **Caveman Compress** | Compresses memory files | Input tokens (context on startup) | ~45% |

Both components are independent — use one or both.

## Structure

```
plugin/
├── caveman/
│   └── SKILL.md                    ← model instructions (rules, triggers, examples)
│
└── caveman_compress/
    ├── SKILL.md                    ← model instructions (when/how to run pipeline)
    ├── hooks/
    │   ├── post-save.py            ← auto-compress hook (cross-platform)
    │   ├── post-save.sh            ← auto-compress hook (bash, legacy)
    │   └── settings-example.json  ← Claude Code hook configuration example
    └── scripts/
        ├── __main__.py             ← CLI entry point (subcommands)
        ├── compress.py             ← pipeline orchestration, Claude API calls
        ├── detect.py               ← file classification (compress / skip)
        ├── validate.py             ← local output validation, no tokens
        ├── audit.py                ← scan project, verbosity score, savings estimate
        ├── undo.py                 ← restore from .original backup
        ├── stats.py                ← savings stats across all compressed files
        └── diff.py                 ← paragraph-level diff: original vs compressed
```

## Requirements

- **Caveman mode:** none (SKILL.md only)
- **Caveman Compress:** Python 3.10+, Claude Code CLI in PATH

## Caveman mode

```
/caveman          # full (default) — remove articles, filler, hedging
/caveman lite     # remove filler, keep grammar intact
/caveman ultra    # maximum compression, telegraphic
```

Deactivate: `stop caveman` or `normal mode`

## Caveman Compress — commands

```
# Compress
/caveman-compress CLAUDE.md
/caveman-compress docs/
/caveman-compress "*.md"

# Audit (no writes — see what would be compressed)
/caveman-audit
/caveman-audit docs/ --min-savings 25

# Stats (savings across all compressed files)
/caveman-stats

# Diff (what did compression change?)
/caveman-diff CLAUDE.md

# Undo (restore from backup)
/caveman-undo CLAUDE.md
```

Or run directly via Python:

```bash
python -m plugin.caveman_compress.scripts compress CLAUDE.md
python -m plugin.caveman_compress.scripts compress docs/ --min-savings 30
python -m plugin.caveman_compress.scripts audit
python -m plugin.caveman_compress.scripts stats
python -m plugin.caveman_compress.scripts diff CLAUDE.md
python -m plugin.caveman_compress.scripts undo CLAUDE.md
```

### Edit workflow

1. Edit `CLAUDE.original.md` (the readable version)
2. Run `/caveman-compress CLAUDE.md` again — or let the hook do it automatically

Never edit the compressed file directly — changes will be lost on next compress.

## Compress hook (auto-compress on save)

The hook watches for edits to `.original.*` files and automatically re-compresses.

**Setup:**

Copy the hook config into your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python plugin/caveman_compress/hooks/post-save.py"
          }
        ]
      }
    ]
  }
}
```

After that, every time Claude edits a `.original.md` file, the compressed version is regenerated automatically.

> The hook is a Python script -- works on Windows, macOS, and Linux without extra dependencies.
