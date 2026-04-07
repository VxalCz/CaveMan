# Caveman Compress

## Triggers

| User says | Action |
|-----------|--------|
| `/caveman-compress <file>` | Compress one file |
| `/caveman-compress <dir>` or `*.md` | Batch compress |
| `/caveman-audit` or `/caveman-audit <dir>` | Audit — scan, no writes |
| `/caveman-undo <file>` | Restore from backup |
| `/caveman-stats` or `/caveman-stats <dir>` | Show savings stats |
| `/caveman-diff <file>` | Paragraph diff: original vs compressed |

## How to run

```
# Compress single file
python -m plugin.caveman_compress.scripts compress CLAUDE.md

# Batch: directory or glob
python -m plugin.caveman_compress.scripts compress docs/
python -m plugin.caveman_compress.scripts compress "*.md"

# Skip files where savings would be < 30%
python -m plugin.caveman_compress.scripts compress CLAUDE.md --min-savings 30

# Audit (no writes)
python -m plugin.caveman_compress.scripts audit
python -m plugin.caveman_compress.scripts audit . --min-savings 20

# Undo
python -m plugin.caveman_compress.scripts undo CLAUDE.md

# Stats
python -m plugin.caveman_compress.scripts stats

# Diff
python -m plugin.caveman_compress.scripts diff CLAUDE.md
```

Report the result to the user: tokens before/after, savings %, any warnings.

## What this does

Compresses a markdown/text file to save input tokens on every future session load.
Preserves a human-readable backup.

Result:
- `<file>` ← compressed version (Claude reads this each session)
- `<file>.original.<ext>` ← readable backup (human edits this)

## Edit workflow

1. Edit `<file>.original.<ext>` (the readable version)
2. Run `/caveman-compress <file>` again
3. Compressed file is overwritten with the new version

Never edit the compressed file directly — changes will be lost on next compress run.

## What gets compressed

**Yes:** natural language — sentences, paragraphs, descriptions, instructions

**Never:**
- Code blocks (``` fenced or indented ```)
- Inline code (`backtick content`)
- URLs and markdown links
- File paths (`/src/components/...`, `./config.yaml`)
- Shell commands (`npm install`, `git commit`)
- Technical terms, library names, APIs
- Proper nouns (projects, companies, people)
- Headings (kept verbatim — text under them is compressed)
- Table structure (kept — cell text is compressed)
- Dates, version numbers, numeric values
- Environment variables (`$HOME`, `NODE_ENV`)
- YAML frontmatter in markdown files
