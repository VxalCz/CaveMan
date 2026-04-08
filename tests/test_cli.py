"""Tests for __main__.py CLI dispatch and argument parsing."""

import pytest
from unittest.mock import patch, MagicMock

from plugin.caveman_compress.scripts.__main__ import main, _resolve_targets
from pathlib import Path


# ── _resolve_targets ─────────────────────────────────────────────────────────

def test_resolve_targets_file(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello")
    targets = _resolve_targets([str(f)])
    assert targets == [f]


def test_resolve_targets_directory(tmp_path):
    (tmp_path / "a.md").write_text("aaa")
    (tmp_path / "b.txt").write_text("bbb")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("ccc")
    targets = _resolve_targets([str(tmp_path)])
    names = [t.name for t in targets]
    assert "a.md" in names
    assert "b.txt" in names
    assert "c.md" in names


def test_resolve_targets_glob(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "one.md").write_text("1")
    (tmp_path / "two.md").write_text("2")
    (tmp_path / "skip.py").write_text("3")
    targets = _resolve_targets(["*.md"])
    names = [t.name for t in targets]
    assert "one.md" in names
    assert "two.md" in names
    assert "skip.py" not in names


def test_resolve_targets_nonexistent():
    targets = _resolve_targets(["/nonexistent/file.md"])
    assert len(targets) == 1  # returns it anyway, compress_file will handle error


# ── CLI dispatch ─────────────────────────────────────────────────────────────

def test_no_command_returns_1(monkeypatch):
    monkeypatch.setattr("sys.argv", ["caveman-compress"])
    assert main() == 1


def test_compress_dispatch(tmp_path, monkeypatch):
    f = tmp_path / "test.md"
    f.write_text("Some verbose text here.")

    monkeypatch.setattr("sys.argv", [
        "caveman-compress", "compress", str(f), "--quiet"
    ])

    with patch(
        "plugin.caveman_compress.scripts.compress.compress_file",
        return_value=True,
    ) as mock:
        result = main()

    assert result == 0
    mock.assert_called_once()
    call_kwargs = mock.call_args
    assert call_kwargs.kwargs.get("min_savings") == 20  # default


def test_compress_with_model_and_dry_run(tmp_path, monkeypatch):
    f = tmp_path / "test.md"
    f.write_text("Text")

    monkeypatch.setattr("sys.argv", [
        "caveman-compress", "compress", str(f),
        "--model", "claude-haiku-4-5-20251001",
        "--dry-run", "--quiet",
    ])

    with patch(
        "plugin.caveman_compress.scripts.compress.compress_file",
        return_value=True,
    ) as mock:
        result = main()

    assert result == 0
    call_kwargs = mock.call_args
    assert call_kwargs.kwargs.get("model") == "claude-haiku-4-5-20251001"
    assert call_kwargs.kwargs.get("dry_run") is True


def test_audit_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", [
        "caveman-compress", "audit", str(tmp_path)
    ])

    with patch(
        "plugin.caveman_compress.scripts.audit.audit_directory",
        return_value=[],
    ), patch(
        "plugin.caveman_compress.scripts.audit.print_audit_table",
    ):
        result = main()

    assert result == 0


def test_undo_dispatch(tmp_path, monkeypatch):
    f = tmp_path / "test.md"
    f.write_text("compressed")
    backup = tmp_path / "test.original.md"
    backup.write_text("original")

    monkeypatch.setattr("sys.argv", [
        "caveman-compress", "undo", str(f), "--quiet"
    ])

    result = main()
    assert result == 0
    assert f.read_text() == "original"


def test_stats_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", [
        "caveman-compress", "stats", str(tmp_path)
    ])

    with patch(
        "plugin.caveman_compress.scripts.stats.collect_stats",
        return_value=[],
    ), patch(
        "plugin.caveman_compress.scripts.stats.print_stats",
    ):
        result = main()

    assert result == 0


def test_diff_dispatch(tmp_path, monkeypatch):
    f = tmp_path / "test.md"
    f.write_text("compressed")
    backup = tmp_path / "test.original.md"
    backup.write_text("original text here")

    monkeypatch.setattr("sys.argv", [
        "caveman-compress", "diff", str(f)
    ])

    result = main()
    assert result == 0
