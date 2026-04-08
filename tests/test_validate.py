from plugin.caveman_compress.scripts.validate import validate

ORIGINAL = """\
# Introduction

This is a long and verbose introduction to the topic at hand.

## Details

Some detailed explanation here with quite a lot of words.

```python
def foo():
    return 42
```

Visit https://example.com for more information.

- First item in the list
- Second item in the list
- Third item in the list
"""

GOOD_COMPRESSED = """\
# Introduction

Brief intro to the topic.

## Details

Detailed explanation.

```python
def foo():
    return 42
```

Visit https://example.com for more information.

- First item
- Second item
- Third item
"""


def test_valid_compression_passes():
    result = validate(ORIGINAL, GOOD_COMPRESSED)
    assert result.ok, str(result)


def test_missing_heading_is_error():
    compressed = GOOD_COMPRESSED.replace("## Details\n", "")
    result = validate(ORIGINAL, compressed)
    assert not result.ok
    assert any("Heading" in e for e in result.errors)


def test_changed_heading_text_is_error():
    compressed = GOOD_COMPRESSED.replace("## Details", "## Info")
    result = validate(ORIGINAL, compressed)
    assert not result.ok
    assert any("Details" in e or "Heading" in e for e in result.errors)


def test_modified_code_block_is_error():
    compressed = GOOD_COMPRESSED.replace("return 42", "return 99")
    result = validate(ORIGINAL, compressed)
    assert not result.ok
    assert any("Code block" in e for e in result.errors)


def test_missing_url_is_error():
    compressed = GOOD_COMPRESSED.replace("https://example.com", "the site")
    result = validate(ORIGINAL, compressed)
    assert not result.ok
    assert any("example.com" in e for e in result.errors)


def test_missing_bullets_is_warning_not_error():
    # Remove one bullet — within ±15% tolerance (3→2 = 67%, outside)
    compressed = GOOD_COMPRESSED.replace("- Second item\n", "")
    result = validate(ORIGINAL, compressed)
    # Should be a warning, not a blocking error
    assert any("Bullet" in w or "bullet" in w for w in result.warnings)


def test_no_changes_passes():
    result = validate(ORIGINAL, ORIGINAL)
    assert result.ok


def test_multiple_code_blocks():
    text = """\
# Doc

```bash
echo hello
```

Middle text.

```python
x = 1
```
"""
    compressed = """\
# Doc

```bash
echo hello
```

Mid text.

```python
x = 1
```
"""
    result = validate(text, compressed)
    assert result.ok


def test_code_block_count_mismatch():
    compressed = GOOD_COMPRESSED.replace(
        "```python\ndef foo():\n    return 42\n```\n", ""
    )
    result = validate(ORIGINAL, compressed)
    assert not result.ok
    assert any("Code block" in e for e in result.errors)


# ── Frontmatter validation ───────────────────────────────────────────────────

FRONTMATTER_ORIGINAL = """\
---
title: My Doc
version: 1.0
---

# Heading

This is a very verbose and unnecessarily long description of the content.
"""

FRONTMATTER_GOOD = """\
---
title: My Doc
version: 1.0
---

# Heading

Brief description of content.
"""


def test_frontmatter_preserved_passes():
    result = validate(FRONTMATTER_ORIGINAL, FRONTMATTER_GOOD)
    assert result.ok, str(result)


def test_frontmatter_removed_is_error():
    compressed = "# Heading\n\nBrief description of content.\n"
    result = validate(FRONTMATTER_ORIGINAL, compressed)
    assert not result.ok
    assert any("frontmatter" in e.lower() for e in result.errors)


def test_frontmatter_modified_is_error():
    compressed = FRONTMATTER_ORIGINAL.replace("version: 1.0", "version: 2.0")
    result = validate(FRONTMATTER_ORIGINAL, compressed)
    assert not result.ok
    assert any("frontmatter" in e.lower() for e in result.errors)


def test_no_frontmatter_no_error():
    """Files without frontmatter should not trigger frontmatter errors."""
    result = validate(ORIGINAL, GOOD_COMPRESSED)
    assert not any("frontmatter" in e.lower() for e in result.errors)


# ── Table validation ─────────────────────────────────────────────────────────

TABLE_ORIGINAL = """\
# Config

| Option | Default | Description |
|--------|---------|-------------|
| debug  | false   | Enable debug mode for verbose logging |
| port   | 3000    | The port number to listen on |
"""

TABLE_GOOD = """\
# Config

| Option | Default | Description |
|--------|---------|-------------|
| debug  | false   | Enable debug mode |
| port   | 3000    | Port to listen on |
"""


def test_table_rows_preserved_passes():
    result = validate(TABLE_ORIGINAL, TABLE_GOOD)
    assert result.ok, str(result)


def test_table_row_removed_is_warning():
    compressed = """\
# Config

| Option | Default | Description |
|--------|---------|-------------|
| debug  | false   | Enable debug mode |
"""
    result = validate(TABLE_ORIGINAL, compressed)
    assert any("table" in w.lower() for w in result.warnings)
