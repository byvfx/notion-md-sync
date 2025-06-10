"""
Integration tests for notion-md-sync.
"""

import os
import tempfile
import pytest
from notion_md_sync.markdown_parser import MarkdownParser
from notion_md_sync.block_converter import BlockConverter


def test_markdown_to_blocks_conversion():
    """Test converting markdown to Notion blocks and back."""
    # Test markdown content
    markdown_content = """# Test Heading

This is a paragraph with **bold** and *italic* text.

## Secondary Heading

- List item 1
- List item 2

> This is a quote

```python
def hello_world():
    print("Hello, world!")
```

1. Numbered item 1
2. Numbered item 2
"""
    
    # Parse markdown
    parser = MarkdownParser()
    converter = BlockConverter()
    
    # Convert to blocks
    blocks = converter.markdown_to_blocks(markdown_content)
    
    # Check blocks
    assert len(blocks) > 0
    
    # Find heading blocks
    heading_blocks = [b for b in blocks if b["type"].startswith("heading_")]
    assert len(heading_blocks) == 2
    assert heading_blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Test Heading"
    
    # Find paragraph blocks
    paragraph_blocks = [b for b in blocks if b["type"] == "paragraph"]
    assert len(paragraph_blocks) > 0
    
    # Find list blocks
    list_blocks = [b for b in blocks if b["type"] == "bulleted_list_item"]
    assert len(list_blocks) == 2
    
    # Find code block
    code_blocks = [b for b in blocks if b["type"] == "code"]
    assert len(code_blocks) == 1
    assert "hello_world" in code_blocks[0]["code"]["rich_text"][0]["text"]["content"]
    
    # Convert back to markdown
    markdown_output = converter.blocks_to_markdown(blocks)
    
    # Check that main elements are in the output
    assert "# Test Heading" in markdown_output
    assert "## Secondary Heading" in markdown_output
    assert "List item" in markdown_output
    assert "This is a quote" in markdown_output
    assert "def hello_world" in markdown_output
    assert "Numbered item" in markdown_output


def test_frontmatter_roundtrip():
    """Test roundtrip of markdown with frontmatter."""
    # Create a temporary markdown file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""---
title: Test Document
notion_page_id: abc123
tags:
  - test
  - integration
---

# Test Document

This is a test document for integration testing.
""")
        file_path = f.name
    
    try:
        parser = MarkdownParser()
        
        # Parse the file
        metadata, html, raw = parser.parse_file(file_path)
        
        # Check metadata
        assert metadata["title"] == "Test Document"
        assert metadata["notion_page_id"] == "abc123"
        assert metadata["tags"] == ["test", "integration"]
        
        # Update metadata
        parser.update_frontmatter(file_path, {
            "last_synced": "2023-06-09T10:00:00",
            "status": "synced"
        })
        
        # Read again
        updated_metadata, _, _ = parser.parse_file(file_path)
        
        # Check updated metadata
        assert updated_metadata["title"] == "Test Document"
        assert updated_metadata["last_synced"] == "2023-06-09T10:00:00"
        assert updated_metadata["status"] == "synced"
        assert updated_metadata["tags"] == ["test", "integration"]
        
    finally:
        os.unlink(file_path)