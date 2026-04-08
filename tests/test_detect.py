from plugin.caveman_compress.scripts.detect import should_compress


def test_compressible_extensions(tmp_path):
    for ext in (".md", ".txt", ".rst", ".markdown"):
        f = tmp_path / f"file{ext}"
        f.write_text("Some natural language text here.")
        ok, reason = should_compress(f)
        assert ok, f"{ext}: {reason}"


def test_code_extensions_skipped(tmp_path):
    for ext in (".py", ".js", ".ts", ".json", ".yaml", ".sh", ".go"):
        f = tmp_path / f"file{ext}"
        f.write_text("x = 1")
        ok, reason = should_compress(f)
        assert not ok, f"{ext} should be skipped"


def test_backup_files_skipped(tmp_path):
    f = tmp_path / "CLAUDE.original.md"
    f.write_text("Some text.")
    ok, reason = should_compress(f)
    assert not ok
    assert "Backup" in reason


def test_missing_file():
    ok, reason = should_compress("/nonexistent/file.md")
    assert not ok
    assert "not found" in reason


def test_extensionless_json_skipped(tmp_path):
    f = tmp_path / "config"
    f.write_text('{"key": "value", "num": 42}')
    ok, reason = should_compress(f)
    assert not ok
    assert "JSON" in reason


def test_extensionless_yaml_skipped(tmp_path):
    lines = "\n".join(f"key{i}: value{i}" for i in range(20))
    f = tmp_path / "config"
    f.write_text(lines)
    ok, reason = should_compress(f)
    assert not ok
    assert "YAML" in reason


def test_extensionless_code_skipped(tmp_path):
    code = "\n".join([
        "import os", "import sys", "def main():", "    pass",
        "class Foo:", "    def bar(self): pass",
        "const x = 1", "function foo() {}", "return x",
        "for i in range(10):", "    print(i)",
    ])
    f = tmp_path / "script"
    f.write_text(code)
    ok, reason = should_compress(f)
    assert not ok
    assert "code" in reason


def test_extensionless_prose_compressible(tmp_path):
    prose = (
        "This is a long document written in natural language. "
        "It contains many sentences and paragraphs. "
        "The content is descriptive and explains various concepts. "
        "There are no code patterns here at all.\n\n"
        "Another paragraph with more natural language text. "
        "This should be detected as prose and marked for compression."
    ) * 3
    f = tmp_path / "NOTES"
    f.write_text(prose)
    ok, reason = should_compress(f)
    assert ok, reason


def test_empty_file_skipped(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("")
    ok, reason = should_compress(f)
    assert not ok
