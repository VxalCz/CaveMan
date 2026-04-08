"""
Caveman Compress — CLI entry point.

Subcommands:
    compress <path> [path …]   Compress one or more files / directories
    audit    [directory]        Scan for compressible files (no writes)
    undo     <file>             Restore file from .original backup
    stats    [directory]        Show savings across all compressed files
    diff     <file>             Paragraph-level diff: original vs compressed
"""

import argparse
import sys
from pathlib import Path


def _resolve_targets(paths: list[str]) -> list[Path]:
    """
    Expand a list of paths that may include directories and globs.
    Returns a flat list of existing files.
    """
    import glob as _glob

    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for child in sorted(p.rglob("*")):
                if child.is_file():
                    files.append(child)
        elif "*" in raw or "?" in raw:
            for match in sorted(_glob.glob(raw, recursive=True)):
                mp = Path(match)
                if mp.is_file():
                    files.append(mp)
        else:
            files.append(p)
    return files


def cmd_compress(args: argparse.Namespace) -> int:
    from .compress import compress_file

    targets = _resolve_targets(args.paths)
    if not targets:
        print("Error: no files specified.", file=sys.stderr)
        return 1

    success_count = skip_count = 0
    for path in targets:
        ok = compress_file(
            path,
            verbose=not args.quiet,
            min_savings=args.min_savings,
            model=args.model,
            dry_run=args.dry_run,
        )
        if ok:
            success_count += 1
        else:
            skip_count += 1

    if len(targets) > 1 and not args.quiet:
        print(f"\nDone: {success_count} compressed, {skip_count} skipped")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    from .audit import audit_directory, print_audit_table

    root = Path(args.directory).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {args.directory}", file=sys.stderr)
        return 1

    records = audit_directory(root, min_savings=args.min_savings)
    print_audit_table(records, root, json=args.json)
    return 0


def cmd_undo(args: argparse.Namespace) -> int:
    from .undo import undo_file

    ok = undo_file(args.file, verbose=not args.quiet)
    return 0 if ok else 1


def cmd_stats(args: argparse.Namespace) -> int:
    from .stats import collect_stats, print_stats

    root = Path(args.directory).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {args.directory}", file=sys.stderr)
        return 1

    records = collect_stats(root)
    print_stats(records, json=args.json)
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    from .diff import diff_file

    ok = diff_file(args.file)
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="caveman-compress",
        description="Compress markdown/text files to save context tokens.",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    # ── compress ──────────────────────────────────────────────────────────────
    p_compress = sub.add_parser(
        "compress", help="Compress one or more files or directories"
    )
    p_compress.add_argument(
        "paths", nargs="+", metavar="path",
        help="Files, directories, or glob patterns to compress",
    )
    p_compress.add_argument(
        "--min-savings", "-s", type=int, default=20, metavar="PCT",
        help="Skip files where estimated savings < PCT%% (default: 20)",
    )
    p_compress.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )
    p_compress.add_argument(
        "--model", "-m", type=str, default=None, metavar="MODEL",
        help="Claude model to use for compression (e.g. claude-haiku-4-5-20251001)",
    )
    p_compress.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Print compressed output to stdout without writing files",
    )

    # ── audit ─────────────────────────────────────────────────────────────────
    p_audit = sub.add_parser(
        "audit", help="Scan for compressible files (no writes)"
    )
    p_audit.add_argument(
        "directory", nargs="?", default=".",
        help="Directory to scan (default: current directory)",
    )
    p_audit.add_argument(
        "--min-savings", "-s", type=int, default=0, metavar="PCT",
        help="Only show files with estimated savings >= PCT%%",
    )
    p_audit.add_argument(
        "--json", action="store_true",
        help="Output results as JSON instead of a table",
    )

    # ── undo ──────────────────────────────────────────────────────────────────
    p_undo = sub.add_parser("undo", help="Restore file from .original backup")
    p_undo.add_argument("file", help="Compressed file to restore")
    p_undo.add_argument("--quiet", "-q", action="store_true")

    # ── stats ─────────────────────────────────────────────────────────────────
    p_stats = sub.add_parser(
        "stats", help="Show token savings across all compressed files"
    )
    p_stats.add_argument(
        "directory", nargs="?", default=".",
        help="Directory to scan (default: current directory)",
    )
    p_stats.add_argument(
        "--json", action="store_true",
        help="Output results as JSON instead of a table",
    )

    # ── diff ──────────────────────────────────────────────────────────────────
    p_diff = sub.add_parser(
        "diff", help="Paragraph-level diff: original vs compressed"
    )
    p_diff.add_argument("file", help="Compressed file to diff")

    # ── dispatch ──────────────────────────────────────────────────────────────
    args = parser.parse_args()

    dispatch = {
        "compress": cmd_compress,
        "audit": cmd_audit,
        "undo": cmd_undo,
        "stats": cmd_stats,
        "diff": cmd_diff,
    }

    if args.command not in dispatch:
        parser.print_help()
        return 1

    return dispatch[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
