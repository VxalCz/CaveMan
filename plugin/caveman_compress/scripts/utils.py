"""Shared utilities for caveman-compress scripts."""


def count_tokens_approx(text: str) -> int:
    """Rough token estimate: ~4 chars per token.

    This is a simple heuristic based on average English tokenization.
    Actual token counts vary by model and language:
    - English prose: ~4 chars/token (reasonably accurate)
    - Czech/diacritics: ~3 chars/token (this function overestimates savings by ~20-30%)
    - Code-heavy text: ~3.5 chars/token

    For precise counts, use tiktoken or the model's tokenizer.
    For the purpose of savings estimation and comparison, the approximation
    is consistent enough to be useful.
    """
    return max(1, len(text) // 4)
