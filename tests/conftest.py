"""Shared fixtures for caveman-compress tests."""


import pytest

VERBOSE_TEXT = """\
# Configuration

I would strongly recommend that you make sure to use TypeScript with strict mode
enabled for all new code. Please don't use the `any` type unless there's
genuinely absolutely no way around it, and if you actually do use it,
make sure to leave a comment that basically explains the reasoning behind
your decision. I find that really taking the time to properly type things
essentially catches quite a lot of bugs before they ever actually make it
to runtime, so it's definitely worth doing.
"""

DENSE_TEXT = """\
# Config

Use TypeScript strict mode. No `any` -- comment why if unavoidable.
Types catch bugs early. Prefer short names.
"""

COMPRESSED_TEXT = """\
# Configuration

Use TypeScript strict mode. No `any` unless unavoidable -- comment reasoning.
Proper typing catches bugs before runtime.
"""


@pytest.fixture
def verbose_md(tmp_path):
    """Create a verbose markdown file for testing."""
    f = tmp_path / "doc.md"
    f.write_text(VERBOSE_TEXT, encoding="utf-8")
    return f


@pytest.fixture
def dense_md(tmp_path):
    """Create a dense/already-compressed markdown file for testing."""
    f = tmp_path / "doc.md"
    f.write_text(DENSE_TEXT, encoding="utf-8")
    return f


@pytest.fixture
def compressed_pair(tmp_path):
    """Create a compressed file with its .original backup."""
    compressed = tmp_path / "doc.md"
    backup = tmp_path / "doc.original.md"
    compressed.write_text(COMPRESSED_TEXT, encoding="utf-8")
    backup.write_text(VERBOSE_TEXT, encoding="utf-8")
    return compressed, backup
