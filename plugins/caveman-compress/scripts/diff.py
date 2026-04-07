"""
/caveman-diff <file> — paragraph-level diff between compressed file and its
.original backup. Shows what compression changed.
"""

import difflib
import re
import sys
from pathlib import Path

BACKUP_RE = re.compile(r"^(.+)\.original(\.[^.]+)?$")


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs (double newline boundaries)."""
    # Normalise line endings, then split on blank lines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n{2,}", text)
    return [b.strip() for b in blocks if b.strip()]


def _find_backup(path: Path) -> Path | None:
    suffix = path.suffix or ""
    stem = path.stem if suffix else path.name
    backup_name = f"{stem}.original{suffix}" if suffix else f"{stem}.original"
    backup = path.parent / backup_name
    return backup if backup.exists() else None


def diff_file(filepath: str | Path, context: int = 1) -> bool:
    """
    Print a paragraph-level diff for the given compressed file.
    Returns True on success.
    """
    path = Path(filepath).resolve()

    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        return False

    backup_path = _find_backup(path)
    if backup_path is None:
        print(
            f"No backup found for {path.name}.\n"
            f"(Only files compressed with caveman-compress have a diff.)",
            file=sys.stderr,
        )
        return False

    original_text = backup_path.read_text(encoding="utf-8", errors="replace")
    compressed_text = path.read_text(encoding="utf-8", errors="replace")

    orig_paras = _split_paragraphs(original_text)
    comp_paras = _split_paragraphs(compressed_text)

    matcher = difflib.SequenceMatcher(None, orig_paras, comp_paras, autojunk=False)
    opcodes = matcher.get_opcodes()

    orig_tokens = max(1, len(original_text) // 4)
    comp_tokens = max(1, len(compressed_text) // 4)
    saved = orig_tokens - comp_tokens
    pct = int(100 * saved / orig_tokens)

    print(f"Diff: {backup_path.name}  ->  {path.name}")
    print(f"Tokens: {orig_tokens} -> {comp_tokens}  ({pct}% saved, ~{saved} tokens)")
    print()

    has_changes = any(tag != "equal" for tag, *_ in opcodes)
    if not has_changes:
        print("No differences found.")
        return True

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            # Show context paragraphs (trimmed if long)
            for para in orig_paras[i1:i2]:
                preview = para[:80] + "..." if len(para) > 80 else para
                print(f"  {preview}")
            continue

        if tag in ("replace", "delete"):
            for para in orig_paras[i1:i2]:
                for line in para.splitlines():
                    print(f"- {line}")
            if tag == "replace":
                print()

        if tag in ("replace", "insert"):
            for para in comp_paras[j1:j2]:
                for line in para.splitlines():
                    print(f"+ {line}")

        print()

    return True
