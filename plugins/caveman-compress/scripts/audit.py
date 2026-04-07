"""
/caveman-audit — scan project for compressible files.

Reports a table: file, current tokens, verbosity score, estimated savings.
Pure local analysis, no API calls.
"""

import re
from pathlib import Path

from .detect import should_compress

# Filler words used for verbosity scoring
FILLER_WORDS = {
    # English
    "just", "really", "basically", "actually", "simply", "essentially",
    "quite", "very", "sure", "certainly", "obviously", "clearly", "totally",
    "literally", "honestly", "frankly", "absolutely", "definitely",
    "however", "furthermore", "additionally", "moreover",
    "in order to", "make sure to", "remember to", "you should",
    "it is worth noting", "it should be noted", "please note",
    "i would recommend", "i would suggest", "you might want to",
    "feel free to", "don't hesitate to",
    # Czech
    "prostě", "vlastně", "v podstatě", "zkrátka", "jednoduše", "v zásadě",
    "docela", "celkem", "nicméně", "kromě toho", "navíc", "dále",
    "samozřejmě", "určitě", "rozhodně", "upřímně", "opravdu",
    "doporučoval bych", "měl bys", "nezapomeň",
}

FILLER_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in FILLER_WORDS) + r")\b",
    re.IGNORECASE,
)

# Strip code blocks before scoring so we don't penalise technical content
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```|`[^`]+`")
SENTENCE_END_RE = re.compile(r"[.!?]+")


def _strip_code(text: str) -> str:
    return CODE_BLOCK_RE.sub(" ", text)


def verbosity_score(text: str) -> int:
    """
    Return a verbosity score 1–10.
    1 = already dense, 10 = extremely verbose.
    """
    clean = _strip_code(text)
    words = clean.split()
    if not words:
        return 1

    # Filler density
    filler_count = len(FILLER_RE.findall(clean))
    filler_ratio = filler_count / len(words)

    # Average sentence length (longer → more likely to have filler)
    sentences = [s.strip() for s in SENTENCE_END_RE.split(clean) if s.strip()]
    avg_sentence_len = (
        sum(len(s.split()) for s in sentences) / len(sentences)
        if sentences else 0
    )
    # Normalise: 10 words = tight, 30+ words = verbose
    length_factor = min(1.0, max(0.0, (avg_sentence_len - 10) / 20))

    raw = filler_ratio * 0.6 + length_factor * 0.4
    # Map 0–0.25 → 1–10
    score = int(1 + min(raw / 0.25, 1.0) * 9)
    return score


def estimated_savings(score: int) -> int:
    """
    Rough savings % estimate based on verbosity score.
    Derived from benchmark data (38–60% range for typical files).
    """
    # score 1 → ~15%, score 10 → ~60%
    return int(15 + (score - 1) * (45 / 9))


def _count_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def audit_directory(root: str | Path, min_savings: int = 0) -> list[dict]:
    """
    Walk `root` recursively and return audit records for compressible files.
    Each record: {path, tokens, score, savings_pct, already_compressed}
    """
    root = Path(root).resolve()
    results = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        ok, _ = should_compress(path)
        if not ok:
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        tokens = _count_tokens(text)
        score = verbosity_score(text)
        savings = estimated_savings(score)

        if savings < min_savings:
            continue

        # Check if a compressed version already exists
        suffix = path.suffix or ""
        stem = path.stem if suffix else path.name
        backup_name = f"{stem}.original{suffix}" if suffix else f"{stem}.original"
        already_compressed = (path.parent / backup_name).exists()

        results.append(
            {
                "path": path.relative_to(root),
                "tokens": tokens,
                "score": score,
                "savings_pct": savings,
                "already_compressed": already_compressed,
            }
        )

    return results


def print_audit_table(records: list[dict], root: Path) -> None:
    if not records:
        print("No compressible files found.")
        return

    col_path = max(len(str(r["path"])) for r in records)
    col_path = max(col_path, 4)

    header = (
        f"{'File':<{col_path}}  {'Tokens':>6}  {'Score':>5}  "
        f"{'Est. savings':>12}  {'Status'}"
    )
    print(header)
    print("-" * len(header))

    total_tokens = 0
    total_saved = 0

    for r in records:
        status = "compressed" if r["already_compressed"] else "not compressed"
        saved = int(r["tokens"] * r["savings_pct"] / 100)
        total_tokens += r["tokens"]
        total_saved += saved
        print(
            f"{str(r['path']):<{col_path}}  {r['tokens']:>6}  "
            f"{r['score']:>4}/10  {r['savings_pct']:>10}%  {status}"
        )

    print("-" * len(header))
    pct = int(100 * total_saved / total_tokens) if total_tokens else 0
    print(
        f"{'TOTAL':<{col_path}}  {total_tokens:>6}  {'':>5}  "
        f"{pct:>10}%  ~{total_saved} tokens saveable per session"
    )
