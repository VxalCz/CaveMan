"""
File type detection — decide whether a file should be compressed or skipped.
No tokens consumed here, everything runs locally.
"""

import json
import re
from pathlib import Path

# Extensions that are always compressible (natural language)
COMPRESSIBLE_EXTENSIONS = {".md", ".txt", ".rst", ".markdown"}

# Extensions that are always skipped (code / config)
SKIP_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".yaml", ".yml", ".toml",
    ".env", ".sh", ".bash", ".zsh",
    ".go", ".rs", ".rb", ".java", ".c", ".cpp", ".h",
    ".css", ".scss", ".sass", ".less",
    ".html", ".xml", ".svg",
    ".sql", ".graphql",
    ".lock", ".ini", ".cfg", ".conf",
}

# Backup files created by compress — always skip
BACKUP_PATTERN = re.compile(r"\.original\.[^.]+$")

# Code-like line patterns for extensionless files
CODE_LINE_PATTERNS = re.compile(
    r"^\s*(import |from |def |class |const |let |var |function |#!|"
    r"export |require\(|module\.exports|if |for |while |return |async )"
)

YAML_LINE_PATTERN = re.compile(r"^\s*[\w\-]+\s*:\s*.+")


def should_compress(filepath: str | Path) -> tuple[bool, str]:
    """
    Returns (True, reason) if the file should be compressed,
    or (False, reason) if it should be skipped.
    """
    path = Path(filepath)

    if not path.exists():
        return False, f"File not found: {filepath}"

    if not path.is_file():
        return False, "Not a regular file"

    name = path.name
    suffix = path.suffix.lower()

    # Backup files — skip
    if BACKUP_PATTERN.search(name):
        return False, "Backup file (.original.*) — skipped"

    # Known compressible extension
    if suffix in COMPRESSIBLE_EXTENSIONS:
        if not path.read_text(encoding="utf-8", errors="replace").strip():
            return False, "Empty file"
        return True, f"Compressible extension ({suffix})"

    # Known code/config extension — skip
    if suffix in SKIP_EXTENSIONS:
        return False, f"Code/config extension ({suffix}) — skipped"

    # No extension or unknown — classify by content
    return _classify_by_content(path)


def _classify_by_content(path: Path) -> tuple[bool, str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return False, f"Cannot read file: {e}"

    if not content.strip():
        return False, "Empty file"

    # Try JSON
    try:
        json.loads(content)
        return False, "Detected as JSON — skipped"
    except (json.JSONDecodeError, ValueError):
        pass

    lines = content.splitlines()
    if not lines:
        return False, "Empty file"

    # Count YAML-like lines
    yaml_lines = sum(1 for ln in lines if YAML_LINE_PATTERN.match(ln))
    if yaml_lines / len(lines) > 0.4:
        return False, f"Detected as YAML-like ({yaml_lines}/{len(lines)} lines) — skipped"

    # Count code-like lines
    code_lines = sum(1 for ln in lines if CODE_LINE_PATTERNS.match(ln))
    if code_lines / len(lines) > 0.4:
        return False, f"Detected as code ({code_lines}/{len(lines)} lines) — skipped"

    return True, "Classified as natural language by content"
