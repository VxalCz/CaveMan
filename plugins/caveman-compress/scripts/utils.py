"""Shared utilities for caveman-compress scripts."""

import re

BACKUP_RE = re.compile(r"^(.+)\.original(\.[^.]+)?$")


def _try_tiktoken():
    """Try to load tiktoken encoder. Returns encoder or None."""
    try:
        import tiktoken
        return tiktoken.encoding_for_model("gpt-4")
    except Exception:
        return None


_tiktoken_enc = _try_tiktoken()


def count_tokens_approx(text: str) -> int:
    """Token count: uses tiktoken if available, otherwise ~4 chars/token.

    The tiktoken fallback slightly overestimates savings for Czech/diacritics
    (~3 chars/token) but is consistent enough for comparison purposes.
    """
    if _tiktoken_enc is not None:
        return max(1, len(_tiktoken_enc.encode(text)))
    return max(1, len(text) // 4)
