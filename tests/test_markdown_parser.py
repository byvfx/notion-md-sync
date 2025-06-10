"""
Tests for markdown parser functionality.
"""

import os
import tempfile
import pytest
from notion_md_sync.markdown_parser import MarkdownParser


def test_parse_file():
    """Test parsing a markdown file with frontmatter."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""---
title: Test Document
notion_page_id: abc123
tags:
  - test
  - markdown
---

# Test Heading

This is a paragraph.

- List item 1
- List item 2

```python
def hello():
    print("Hello, world!")
```
        """)
        file_path = f.name
    
    try:
        parser = MarkdownParser()
        metadata, html_content, raw_content = parser.parse_file(file_path)
        
        # Check metadata
        assert metadata["title"] == "Test Document"
        assert metadata["notion_page_id"] == "abc123"
        assert metadata["tags"] == ["test", "markdown"]
        
        # Check content
        assert "# Test Heading" in raw_content
        assert "<h1" in html_content
        assert "<code" in html_content
        assert "<ul" in html_content
    finally:
        os.unlink(file_path)


def test_update_frontmatter():
    """Test updating frontmatter in a markdown file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""---
title: Original Title
tags:
  - original
---

Content here.
        """)
        file_path = f.name
    
    try:
        parser = MarkdownParser()
        
        # Update metadata
        parser.update_frontmatter(file_path, {
            "title": "Updated Title",
            "notion_page_id": "xyz789",
            "tags": ["updated", "new"]
        })
        
        # Read back and verify
        metadata, _, _ = parser.parse_file(file_path)
        assert metadata["title"] == "Updated Title"
        assert metadata["notion_page_id"] == "xyz789"
        assert metadata["tags"] == ["updated", "new"]
    finally:
        os.unlink(file_path)


def test_create_markdown_with_frontmatter():
    """Test creating a new markdown file with frontmatter."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as f:
        file_path = f.name
    
    os.unlink(file_path)  # Delete it so we can create it fresh
    
    try:
        parser = MarkdownParser()
        
        metadata = {
            "title": "New Document",
            "notion_page_id": "def456",
            "last_synced": "2023-06-08T12:34:56"
        }
        
        content = """# New Document

This is a new document created programmatically.

1. Numbered item 1
2. Numbered item 2
"""
        
        parser.create_markdown_with_frontmatter(file_path, metadata, content)
        
        # Read back and verify
        read_metadata, _, read_content = parser.parse_file(file_path)
        assert read_metadata["title"] == "New Document"
        assert read_metadata["notion_page_id"] == "def456"
        assert "# New Document" in read_content
        assert "Numbered item" in read_content
    finally:
        if os.path.exists(file_path):
            os.unlink(file_path)


def test_extract_title():
    """Test extracting title from markdown content."""
    parser = MarkdownParser()
    
    # With H1 title
    content = """# This is the Title

Some content here.
"""
    assert parser.extract_title(content) == "This is the Title"
    
    # Without H1 title
    content = """## Secondary Heading

Some content here.
"""
    assert parser.extract_title(content) is None


def test_extract_headings():
    """Test extracting headings from markdown content."""
    parser = MarkdownParser()
    
    content = """# Main Heading

Some content.

## Secondary Heading

More content.

### Tertiary Heading
"""
    
    headings = parser.extract_headings(content)
    assert len(headings) == 3
    assert headings[0] == (1, "Main Heading")
    assert headings[1] == (2, "Secondary Heading")
    assert headings[2] == (3, "Tertiary Heading")