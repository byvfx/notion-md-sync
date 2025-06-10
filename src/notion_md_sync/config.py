"""
Configuration management for Notion Markdown Sync.
"""

import os
import yaml
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration manager for the application."""

    DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), "config", "config.yaml")

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from file.

        Args:
            config_path: Path to configuration file. If None, uses default path.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config_data = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Dict containing configuration data.
        """
        try:
            with open(self.config_path, "r") as f:
                self.config_data = yaml.safe_load(f) or {}
            return self.config_data
        except FileNotFoundError:
            self.config_data = {}
            return self.config_data

    def save(self) -> None:
        """Save current configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.config_data, f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Priority:
        1. Environment variables (UPPERCASE with _ instead of .)
        2. Configuration file
        3. Default value

        Args:
            key: Configuration key, can use dot notation for nested keys.
            default: Default value if key is not found.

        Returns:
            Configuration value or default.
        """
        # First check environment variables (convert dot notation to uppercase with underscores)
        env_key = key.replace(".", "_").upper()
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
            
        # Then check configuration file
        keys = key.split(".")
        data = self.config_data
        for k in keys:
            if not isinstance(data, dict) or k not in data:
                return default
            data = data[k]
        return data

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key, can use dot notation for nested keys.
            value: Value to set.
        """
        keys = key.split(".")
        data = self.config_data
        for i, k in enumerate(keys[:-1]):
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        # Check required fields
        if not self.get("notion.token"):
            return False
            
        # Check parent page ID if we're syncing to Notion
        sync_direction = self.get("sync.direction")
        if sync_direction in ["markdown_to_notion", "bidirectional"]:
            if not self.get("notion.parent_page_id"):
                return False

        # Check valid options
        valid_directions = ["markdown_to_notion", "notion_to_markdown", "bidirectional"]
        if sync_direction not in valid_directions:
            return False

        return True