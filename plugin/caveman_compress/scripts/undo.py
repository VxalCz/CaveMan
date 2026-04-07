"""
/caveman-undo <file> — restore compressed file from its .original backup.
"""

import sys
from pathlib import Path


def undo_file(filepath: str | Path, verbose: bool = True) -> bool:
    path = Path(filepath).resolve()

    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        return False

    suffix = path.suffix or ""
    stem = path.stem if suffix else path.name
    backup_name = f"{stem}.original{suffix}" if suffix else f"{stem}.original"
    backup_path = path.parent / backup_name

    if not backup_path.exists():
        print(
            f"No backup found: {backup_path.name}\n"
            f"(Only files compressed with caveman-compress have a backup.)",
            file=sys.stderr,
        )
        return False

    original = backup_path.read_text(encoding="utf-8")
    path.write_text(original, encoding="utf-8")

    if verbose:
        print(f"Restored: {path.name}  ←  {backup_path.name}")

    return True
