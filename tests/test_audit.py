from plugin.caveman_compress.scripts.audit import (
    audit_directory,
    estimated_savings,
    verbosity_score,
)

DENSE_TEXT = """\
# Config

Use TypeScript strict mode. No `any` — comment why if unavoidable.
Types catch bugs early. Prefer short names.
"""

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


def test_dense_text_low_score():
    score = verbosity_score(DENSE_TEXT)
    assert 1 <= score <= 4, f"Dense text got score {score}, expected 1-4"


def test_verbose_text_high_score():
    score = verbosity_score(VERBOSE_TEXT)
    assert score >= 6, f"Verbose text got score {score}, expected >=6"


def test_score_range():
    for text in [DENSE_TEXT, VERBOSE_TEXT, "", "One line."]:
        score = verbosity_score(text)
        assert 1 <= score <= 10, f"Score out of range: {score}"


def test_estimated_savings_range():
    for score in range(1, 11):
        savings = estimated_savings(score)
        assert 15 <= savings <= 60, f"Savings {savings} out of range for score {score}"


def test_savings_increases_with_score():
    scores = list(range(1, 11))
    savings = [estimated_savings(s) for s in scores]
    assert savings == sorted(savings), "Savings should increase with verbosity score"


def test_audit_directory_finds_md_files(tmp_path):
    (tmp_path / "notes.md").write_text(VERBOSE_TEXT)
    (tmp_path / "script.py").write_text("def foo(): pass")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "readme.md").write_text(DENSE_TEXT)

    records = audit_directory(tmp_path)
    paths = [str(r["path"]) for r in records]

    assert any("notes.md" in p for p in paths)
    assert any("readme.md" in p for p in paths)
    assert not any(".py" in p for p in paths)


def test_audit_skips_backups(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(VERBOSE_TEXT)
    (tmp_path / "CLAUDE.original.md").write_text(VERBOSE_TEXT)

    records = audit_directory(tmp_path)
    paths = [str(r["path"]) for r in records]
    assert not any("original" in p for p in paths)


def test_audit_marks_already_compressed(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(DENSE_TEXT)
    (tmp_path / "CLAUDE.original.md").write_text(VERBOSE_TEXT)

    records = audit_directory(tmp_path)
    assert len(records) == 1
    assert records[0]["already_compressed"] is True


def test_audit_min_savings_filter(tmp_path):
    (tmp_path / "dense.md").write_text(DENSE_TEXT)
    (tmp_path / "verbose.md").write_text(VERBOSE_TEXT)

    all_records = audit_directory(tmp_path, min_savings=0)
    filtered = audit_directory(tmp_path, min_savings=50)

    assert len(filtered) <= len(all_records)
    for r in filtered:
        assert r["savings_pct"] >= 50
