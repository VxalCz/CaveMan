import pytest
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
