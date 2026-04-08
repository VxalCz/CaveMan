"""
Local validation of compressed output — no tokens consumed.

Checks:
  Errors (block and trigger targeted fix):
    - Headings count and text must match
    - Code blocks must be identical (fenced + indented)
    - URLs must all be preserved
    - YAML frontmatter must be preserved verbatim

  Warnings (logged, not fixed):
    - File paths preserved
    - Bullet count within +-15%
    - Table row count preserved
"""

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        lines = []
        for e in self.errors:
            lines.append(f"  ERROR:   {e}")
        for w in self.warnings:
            lines.append(f"  WARNING: {w}")
        return "\n".join(lines) if lines else "  All checks passed."


# ── Regex patterns ────────────────────────────────────────────────────────────

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)", re.MULTILINE)
FENCED_CODE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INDENTED_CODE_RE = re.compile(r"(?:(?:^|\n)\n)((?:(?:    |\t).+\n?)+)")
URL_RE = re.compile(r"https?://[^\s\)\]\"'>]+")
FILE_PATH_RE = re.compile(r"(?:^|[\s`\"'(])(\.{0,2}/[\w./\-]+\.\w+)")
BULLET_RE = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\n([\s\S]*?)\n---", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|.+\|$", re.MULTILINE)


# ── Extractors ────────────────────────────────────────────────────────────────

def _extract_headings(text: str) -> list[tuple[str, str]]:
    """Return list of (level_hashes, heading_text) tuples."""
    return [(m.group(1), m.group(2).strip()) for m in HEADING_RE.finditer(text)]


def _extract_code_blocks(text: str) -> list[str]:
    """Extract fenced and indented code blocks."""
    fenced = FENCED_CODE_RE.findall(text)
    indented = INDENTED_CODE_RE.findall(text)
    return fenced + indented


def _extract_urls(text: str) -> set[str]:
    return set(URL_RE.findall(text))


def _extract_file_paths(text: str) -> set[str]:
    return set(FILE_PATH_RE.findall(text))


def _count_bullets(text: str) -> int:
    return len(BULLET_RE.findall(text))


def _extract_frontmatter(text: str) -> str | None:
    """Extract YAML frontmatter (between leading --- delimiters)."""
    m = FRONTMATTER_RE.match(text)
    return m.group(0) if m else None


def _count_table_rows(text: str) -> int:
    """Count markdown table rows (lines matching |...|)."""
    return len(TABLE_ROW_RE.findall(text))


# ── Main validator ────────────────────────────────────────────────────────────

def validate(original: str, compressed: str) -> ValidationResult:
    result = ValidationResult()

    # ── Headings ──────────────────────────────────────────────────────────────
    orig_headings = _extract_headings(original)
    comp_headings = _extract_headings(compressed)

    if len(orig_headings) != len(comp_headings):
        result.errors.append(
            f"Heading count mismatch: original={len(orig_headings)}, "
            f"compressed={len(comp_headings)}"
        )
    else:
        for i, (oh, ch) in enumerate(zip(orig_headings, comp_headings)):
            if oh != ch:
                result.errors.append(
                    f"Heading {i+1} changed: "
                    f"'{oh[0]} {oh[1]}' → '{ch[0]} {ch[1]}'"
                )

    # ── Code blocks ───────────────────────────────────────────────────────────
    orig_blocks = _extract_code_blocks(original)
    comp_blocks = _extract_code_blocks(compressed)

    if len(orig_blocks) != len(comp_blocks):
        result.errors.append(
            f"Code block count mismatch: original={len(orig_blocks)}, "
            f"compressed={len(comp_blocks)}"
        )
    else:
        for i, (ob, cb) in enumerate(zip(orig_blocks, comp_blocks)):
            if ob.strip() != cb.strip():
                result.errors.append(f"Code block {i+1} was modified")

    # ── URLs ──────────────────────────────────────────────────────────────────
    orig_urls = _extract_urls(original)
    comp_urls = _extract_urls(compressed)
    missing_urls = orig_urls - comp_urls
    if missing_urls:
        for url in sorted(missing_urls):
            result.errors.append(f"URL missing: {url}")

    # ── File paths (warning only) ─────────────────────────────────────────────
    orig_paths = _extract_file_paths(original)
    comp_paths = _extract_file_paths(compressed)
    missing_paths = orig_paths - comp_paths
    if missing_paths:
        for p in sorted(missing_paths):
            result.warnings.append(f"File path may be missing: {p}")

    # ── YAML frontmatter ────────────────────────────────────────────────────
    orig_fm = _extract_frontmatter(original)
    comp_fm = _extract_frontmatter(compressed)
    if orig_fm is not None:
        if comp_fm is None:
            result.errors.append("YAML frontmatter was removed")
        elif orig_fm.strip() != comp_fm.strip():
            result.errors.append("YAML frontmatter was modified")

    # ── Table rows (warning only) ────────────────────────────────────────────
    orig_table_rows = _count_table_rows(original)
    comp_table_rows = _count_table_rows(compressed)
    if orig_table_rows > 0 and orig_table_rows != comp_table_rows:
        result.warnings.append(
            f"Table row count changed: "
            f"original={orig_table_rows}, compressed={comp_table_rows}"
        )

    # ── Bullet count (warning only, +-15%) ────────────────────────────────────
    orig_bullets = _count_bullets(original)
    comp_bullets = _count_bullets(compressed)
    if orig_bullets > 0:
        ratio = comp_bullets / orig_bullets
        if ratio < 0.85 or ratio > 1.15:
            result.warnings.append(
                f"Bullet count differs significantly: "
                f"original={orig_bullets}, compressed={comp_bullets} "
                f"({ratio:.0%})"
            )

    return result
