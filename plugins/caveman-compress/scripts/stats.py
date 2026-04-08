"""
/caveman-stats — compare all compressed files with their .original backups
and report total token savings per session.
"""

import json as _json
import re
from pathlib import Path

from .utils import count_tokens_approx

BACKUP_RE = re.compile(r"^(.+)\.original(\.[^.]+)?$")


def collect_stats(root: str | Path) -> list[dict]:
    """
    Find all .original.* files under `root`, pair them with their compressed
    counterparts, and return per-file stats.
    """
    root = Path(root).resolve()
    results = []

    for backup_path in sorted(root.rglob("*")):
        if not backup_path.is_file():
            continue

        m = BACKUP_RE.match(backup_path.name)
        if not m:
            continue

        stem, ext = m.group(1), m.group(2) or ""
        compressed_name = f"{stem}{ext}"
        compressed_path = backup_path.parent / compressed_name

        if not compressed_path.exists():
            continue

        original_text = backup_path.read_text(encoding="utf-8", errors="replace")
        compressed_text = compressed_path.read_text(encoding="utf-8", errors="replace")

        orig_tokens = count_tokens_approx(original_text)
        comp_tokens = count_tokens_approx(compressed_text)
        saved = orig_tokens - comp_tokens
        pct = int(100 * saved / orig_tokens) if orig_tokens else 0

        results.append(
            {
                "path": compressed_path.relative_to(root),
                "original_tokens": orig_tokens,
                "compressed_tokens": comp_tokens,
                "saved_tokens": saved,
                "savings_pct": pct,
            }
        )

    return results


def print_stats(records: list[dict], json: bool = False) -> None:
    if json:
        output = [
            {**r, "path": str(r["path"])} for r in records
        ]
        print(_json.dumps(output, indent=2))
        return

    if not records:
        print("No compressed files found. Run /caveman-compress first.")
        return

    col_path = max(len(str(r["path"])) for r in records)
    col_path = max(col_path, 4)

    header = (
        f"{'File':<{col_path}}  {'Original':>8}  {'Compressed':>10}  "
        f"{'Saved':>6}  {'%':>4}"
    )
    print(header)
    print("-" * len(header))

    total_orig = total_comp = total_saved = 0

    for r in records:
        total_orig += r["original_tokens"]
        total_comp += r["compressed_tokens"]
        total_saved += r["saved_tokens"]
        print(
            f"{str(r['path']):<{col_path}}  "
            f"{r['original_tokens']:>8}  "
            f"{r['compressed_tokens']:>10}  "
            f"{r['saved_tokens']:>6}  "
            f"{r['savings_pct']:>3}%"
        )

    print("-" * len(header))
    total_pct = int(100 * total_saved / total_orig) if total_orig else 0
    print(
        f"{'TOTAL':<{col_path}}  {total_orig:>8}  {total_comp:>10}  "
        f"{total_saved:>6}  {total_pct:>3}%"
    )
    print(f"\nSaved per session: ~{total_saved:,} tokens")
