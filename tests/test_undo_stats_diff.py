from plugin.caveman_compress.scripts.diff import _split_paragraphs, diff_file
from plugin.caveman_compress.scripts.stats import collect_stats
from plugin.caveman_compress.scripts.undo import undo_file

ORIGINAL = "This is the original verbose content with many unnecessary words."
COMPRESSED = "Original verbose content."


# ── undo ─────────────────────────────────────────────────────────────────────


def test_undo_restores_file(tmp_path):
    compressed = tmp_path / "CLAUDE.md"
    backup = tmp_path / "CLAUDE.original.md"
    compressed.write_text(COMPRESSED)
    backup.write_text(ORIGINAL)

    ok = undo_file(compressed, verbose=False)
    assert ok
    assert compressed.read_text() == ORIGINAL


def test_undo_no_backup_fails(tmp_path):
    f = tmp_path / "CLAUDE.md"
    f.write_text(COMPRESSED)

    ok = undo_file(f, verbose=False)
    assert not ok


def test_undo_missing_file_fails(tmp_path):
    ok = undo_file(tmp_path / "nonexistent.md", verbose=False)
    assert not ok


def test_undo_extensionless(tmp_path):
    compressed = tmp_path / "NOTES"
    backup = tmp_path / "NOTES.original"
    compressed.write_text(COMPRESSED)
    backup.write_text(ORIGINAL)

    ok = undo_file(compressed, verbose=False)
    assert ok
    assert compressed.read_text() == ORIGINAL


# ── stats ─────────────────────────────────────────────────────────────────────


def test_stats_finds_pairs(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(COMPRESSED)
    (tmp_path / "CLAUDE.original.md").write_text(ORIGINAL)

    records = collect_stats(tmp_path)
    assert len(records) == 1
    r = records[0]
    assert r["original_tokens"] > r["compressed_tokens"]
    assert r["saved_tokens"] > 0
    assert 0 < r["savings_pct"] <= 100


def test_stats_ignores_unpaired(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(COMPRESSED)
    # No .original file — should not appear in stats

    records = collect_stats(tmp_path)
    assert len(records) == 0


def test_stats_multiple_files(tmp_path):
    for name in ("A.md", "B.md", "C.txt"):
        (tmp_path / name).write_text(COMPRESSED)
        stem, ext = name.rsplit(".", 1)
        (tmp_path / f"{stem}.original.{ext}").write_text(ORIGINAL)

    records = collect_stats(tmp_path)
    assert len(records) == 3


def test_stats_recursive(tmp_path):
    sub = tmp_path / "docs"
    sub.mkdir()
    (sub / "notes.md").write_text(COMPRESSED)
    (sub / "notes.original.md").write_text(ORIGINAL)

    records = collect_stats(tmp_path)
    assert len(records) == 1


# ── diff ──────────────────────────────────────────────────────────────────────


def test_split_paragraphs_basic():
    text = "Para one.\n\nPara two.\n\nPara three."
    paras = _split_paragraphs(text)
    assert paras == ["Para one.", "Para two.", "Para three."]


def test_split_paragraphs_extra_blank_lines():
    text = "First.\n\n\n\nSecond."
    paras = _split_paragraphs(text)
    assert paras == ["First.", "Second."]


def test_diff_no_backup_fails(tmp_path, capsys):
    f = tmp_path / "CLAUDE.md"
    f.write_text(COMPRESSED)

    ok = diff_file(f)
    assert not ok


def test_diff_with_backup_succeeds(tmp_path, capsys):
    compressed = tmp_path / "CLAUDE.md"
    backup = tmp_path / "CLAUDE.original.md"
    compressed.write_text(COMPRESSED)
    backup.write_text(ORIGINAL)

    ok = diff_file(compressed)
    assert ok
    out = capsys.readouterr().out
    assert "CLAUDE.md" in out
    assert "tokens" in out.lower()


def test_diff_identical_files(tmp_path, capsys):
    f = tmp_path / "CLAUDE.md"
    backup = tmp_path / "CLAUDE.original.md"
    f.write_text(ORIGINAL)
    backup.write_text(ORIGINAL)

    ok = diff_file(f)
    assert ok
    out = capsys.readouterr().out
    assert "No differences" in out
