"""
Tests for configuration handling.
"""

import os
import tempfile
import pytest
from notion_md_sync.config import Config


def test_config_load_and_get():
    """Test loading config and getting values."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""
notion:
  token: "test_token"
sync:
  direction: "markdown_to_notion"
        """)
        config_path = f.name
    
    try:
        config = Config(config_path)
        
        assert config.get("notion.token") == "test_token"
        assert config.get("sync.direction") == "markdown_to_notion"
        assert config.get("nonexistent") is None
        assert config.get("nonexistent", "default") == "default"
    finally:
        os.unlink(config_path)


def test_config_set_and_save():
    """Test setting config values and saving to file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""
notion:
  token: "test_token"
        """)
        config_path = f.name
    
    try:
        config = Config(config_path)
        
        # Set some values
        config.set("sync.direction", "bidirectional")
        config.set("directories.markdown_root", "/tmp/docs")
        
        # Save to file
        config.save()
        
        # Load again to verify
        config2 = Config(config_path)
        assert config2.get("notion.token") == "test_token"
        assert config2.get("sync.direction") == "bidirectional"
        assert config2.get("directories.markdown_root") == "/tmp/docs"
    finally:
        os.unlink(config_path)


def test_config_validate():
    """Test config validation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("""
notion:
  token: "test_token"
  parent_page_id: "test_page_id"
sync:
  direction: "markdown_to_notion"
        """)
        config_path = f.name
    
    try:
        config = Config(config_path)
        assert config.validate() is True
        
        # Invalid direction
        config.set("sync.direction", "invalid")
        assert config.validate() is False
        
        # Reset direction for next tests
        config.set("sync.direction", "markdown_to_notion")
        
        # No parent page ID
        config.set("notion.parent_page_id", "")
        assert config.validate() is False
        
        # Reset parent page ID
        config.set("notion.parent_page_id", "test_page_id")
        
        # No token
        config.set("notion.token", "")
        assert config.validate() is False
        
        # Direction that doesn't require parent_page_id
        config.set("sync.direction", "notion_to_markdown")
        config.set("notion.token", "test_token")
        config.set("notion.parent_page_id", "")
        assert config.validate() is True
    finally:
        os.unlink(config_path)