"""
Compression pipeline orchestrator.

Flow:
  1. Detect file type (local, no tokens)
  2. Compress via Claude CLI (1 API call)
  3. Validate output (local, no tokens)
     - OK  → save and done
     - Errors → targeted fix via Claude (up to 2 retries)
  4. If still failing → restore original, report error
"""

import subprocess
import sys
from pathlib import Path

from .detect import should_compress
from .utils import count_tokens_approx
from .validate import validate, FENCED_CODE_RE

COMPRESS_SYSTEM_PROMPT = """\
You are a token-efficient text compressor for AI context files.

Rules:
- Compress natural language: remove filler, hedging, pleasantries, redundant phrases
- Use shorter synonyms; fragments are fine
- NEVER touch: code blocks, inline code, URLs, file paths, shell commands, \
technical terms, library names, headings (keep verbatim), table structure, \
dates, version numbers, environment variables, YAML frontmatter
- Output ONLY the compressed text, no commentary
"""

FIX_SYSTEM_PROMPT = """\
You are fixing specific validation errors in a compressed markdown file.
Apply only the targeted fixes listed. Do not re-compress or change anything else.
Output ONLY the corrected full text, no commentary.
"""


def _call_claude(prompt: str, system: str, model: str | None = None) -> str:
    """Call Claude CLI in non-interactive mode, passing prompt via stdin."""
    cmd = ["claude", "-p", "--system-prompt", system]
    if model:
        cmd.extend(["--model", model])
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        raise RuntimeError(
            "Claude CLI not found. Install it and make sure 'claude' is in PATH.\n"
            "See: https://docs.anthropic.com/en/docs/claude-code"
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed (exit {result.returncode}):\n{result.stderr}"
        )
    return result.stdout.strip()


def _compress_text(text: str, model: str | None = None) -> str:
    # Extract fenced code blocks and replace with placeholders before sending.
    # This guarantees code blocks are preserved byte-for-byte regardless of model.
    blocks = FENCED_CODE_RE.findall(text)
    protected = text
    for i, block in enumerate(blocks):
        protected = protected.replace(block, f"{{{{CODE_BLOCK_{i}}}}}", 1)

    prompt = (
        "Compress the following text according to the rules. "
        "Output only the compressed version:\n\n"
        + protected
    )
    compressed = _call_claude(prompt, COMPRESS_SYSTEM_PROMPT, model=model)

    # Restore code blocks
    for i, block in enumerate(blocks):
        compressed = compressed.replace(f"{{{{CODE_BLOCK_{i}}}}}", block, 1)

    return compressed


def _fix_errors(
    compressed: str, errors: list[str], model: str | None = None
) -> str:
    error_list = "\n".join(f"- {e}" for e in errors)
    prompt = (
        f"Fix these validation errors in the compressed text:\n{error_list}\n\n"
        f"Compressed text to fix:\n\n{compressed}"
    )
    return _call_claude(prompt, FIX_SYSTEM_PROMPT, model=model)


def compress_file(
    filepath: str | Path,
    verbose: bool = True,
    min_savings: int = 20,
    model: str | None = None,
    dry_run: bool = False,
) -> bool:
    """
    Compress a file in-place, saving a .original backup.

    min_savings: skip if estimated savings would be below this percentage.
    dry_run: print compressed output to stdout without writing files.
    Returns True on success, False on failure/skip.
    """
    MAX_FILE_SIZE = 100 * 1024  # 100 KB

    path = Path(filepath).resolve()

    # ── Detect ────────────────────────────────────────────────────────────────
    ok, reason = should_compress(path)
    if not ok:
        print(f"Skipped: {reason}", file=sys.stderr)
        return False

    if verbose:
        print(f"Compressing: {path}")

    # ── Determine backup path ─────────────────────────────────────────────────
    suffix = path.suffix or ""
    stem = path.stem if suffix else path.name
    backup_name = f"{stem}.original{suffix}" if suffix else f"{stem}.original"
    backup_path = path.parent / backup_name

    # ── Read source: prefer .original backup if it exists ────────────────────
    if backup_path.exists():
        source_path = backup_path
        if verbose:
            print(f"Source: {backup_path.name} (backup exists)")
    else:
        source_path = path

    if source_path.stat().st_size > MAX_FILE_SIZE:
        print(
            f"Skipped: file too large ({source_path.stat().st_size // 1024} KB, "
            f"limit {MAX_FILE_SIZE // 1024} KB)",
            file=sys.stderr,
        )
        return False

    original_text = source_path.read_text(encoding="utf-8")

    # ── Threshold check (local, no API call) ─────────────────────────────────
    if min_savings > 0:
        from .audit import verbosity_score, estimated_savings
        score = verbosity_score(original_text)
        est = estimated_savings(score)
        if est < min_savings:
            if verbose:
                print(
                    f"Skipped: estimated savings {est}% < threshold {min_savings}%"
                )
            return False

    # ── Compress ──────────────────────────────────────────────────────────────
    try:
        compressed = _compress_text(original_text, model=model)
    except RuntimeError as e:
        print(f"Compression failed: {e}", file=sys.stderr)
        return False

    # ── Validate + fix loop ───────────────────────────────────────────────────
    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES + 1):
        result = validate(original_text, compressed)

        if result.ok:
            break

        if attempt < MAX_RETRIES:
            if verbose:
                print(f"Validation errors (attempt {attempt + 1}), fixing…")
                print(result)
            try:
                compressed = _fix_errors(compressed, result.errors, model=model)
            except RuntimeError as e:
                print(f"Fix attempt failed: {e}", file=sys.stderr)
                return False
        else:
            print(
                f"Validation failed after {MAX_RETRIES} fix attempts. "
                f"Original preserved.",
                file=sys.stderr,
            )
            print(result, file=sys.stderr)
            return False

    if result.warnings and verbose:
        print("Warnings:")
        print(result)

    # ── Report ────────────────────────────────────────────────────────────────
    orig_tokens = count_tokens_approx(original_text)
    comp_tokens = count_tokens_approx(compressed)
    saved_pct = 100 * (1 - comp_tokens / orig_tokens)

    if dry_run:
        print(compressed)
        print(
            f"\n--- dry run: {orig_tokens} -> {comp_tokens} tokens "
            f"({saved_pct:.0f}% saved) ---",
            file=sys.stderr,
        )
        return True

    # ── Save ──────────────────────────────────────────────────────────────────
    # Write backup only if it doesn't already exist
    if not backup_path.exists():
        backup_path.write_text(original_text, encoding="utf-8")
        if verbose:
            print(f"Backup saved: {backup_path.name}")

    path.write_text(compressed, encoding="utf-8")

    if verbose:
        print(
            f"Done: {orig_tokens} -> {comp_tokens} tokens "
            f"({saved_pct:.0f}% saved)"
        )

    return True
