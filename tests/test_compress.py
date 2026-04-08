"""Tests for compress_file: size limit, recompression from .original, dry_run."""

from unittest.mock import patch

import pytest

from plugin.caveman_compress.scripts.compress import compress_file

SAMPLE_TEXT = """\
# Introduction

This is a very verbose and unnecessarily long description that really
should be compressed to save tokens in every future session.
"""

COMPRESSED_TEXT = """\
# Introduction

Verbose description, should be compressed to save tokens.
"""


@pytest.fixture
def sample_md(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text(SAMPLE_TEXT, encoding="utf-8")
    return f


def _mock_compress(text, model=None):
    return COMPRESSED_TEXT


# ── Size limit ───────────────────────────────────────────────────────────────

def test_size_limit_skips_large_file(tmp_path):
    big = tmp_path / "big.md"
    big.write_text("x" * (101 * 1024), encoding="utf-8")
    result = compress_file(big, verbose=False)
    assert result is False


def test_size_limit_allows_small_file(tmp_path):
    small = tmp_path / "small.md"
    small.write_text(SAMPLE_TEXT, encoding="utf-8")
    with patch(
        "plugin.caveman_compress.scripts.compress._compress_text",
        side_effect=_mock_compress,
    ):
        result = compress_file(small, verbose=False, min_savings=0)
    assert result is True


# ── Recompression from .original ─────────────────────────────────────────────

def test_recompress_reads_from_original(tmp_path):
    """When .original backup exists, compress should read from it."""
    doc = tmp_path / "doc.md"
    backup = tmp_path / "doc.original.md"
    doc.write_text("already compressed", encoding="utf-8")
    backup.write_text(SAMPLE_TEXT, encoding="utf-8")

    captured_input = {}

    def spy_compress(text, model=None):
        captured_input["text"] = text
        return COMPRESSED_TEXT

    with patch(
        "plugin.caveman_compress.scripts.compress._compress_text",
        side_effect=spy_compress,
    ):
        result = compress_file(doc, verbose=False, min_savings=0)

    assert result is True
    assert captured_input["text"] == SAMPLE_TEXT


# ── Dry run ──────────────────────────────────────────────────────────────────

def test_dry_run_does_not_write(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    doc.write_text(SAMPLE_TEXT, encoding="utf-8")

    with patch(
        "plugin.caveman_compress.scripts.compress._compress_text",
        side_effect=_mock_compress,
    ):
        result = compress_file(doc, verbose=False, min_savings=0, dry_run=True)

    assert result is True
    # Original file should be unchanged
    assert doc.read_text(encoding="utf-8") == SAMPLE_TEXT
    # No backup should be created
    assert not (tmp_path / "doc.original.md").exists()
    # Compressed text should appear on stdout
    out = capsys.readouterr().out
    assert "Introduction" in out


# ── Model passthrough ────────────────────────────────────────────────────────

def test_model_passed_to_claude(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text(SAMPLE_TEXT, encoding="utf-8")

    captured_model = {}

    def spy_compress(text, model=None):
        captured_model["model"] = model
        return COMPRESSED_TEXT

    with patch(
        "plugin.caveman_compress.scripts.compress._compress_text",
        side_effect=spy_compress,
    ):
        compress_file(
            doc, verbose=False, min_savings=0, model="claude-haiku-4-5-20251001"
        )

    assert captured_model["model"] == "claude-haiku-4-5-20251001"
