"""
Core synchronization logic between markdown files and Notion pages.
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from .notion_client import NotionClient
from .markdown_parser import MarkdownParser
from .block_converter import BlockConverter
from .config import Config


class SyncEngine:
    """Core synchronization engine between markdown files and Notion."""

    def __init__(self, config: Config):
        """
        Initialize the sync engine.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.notion_token = config.get("notion.token")
        self.notion_client = NotionClient(self.notion_token) if self.notion_token else None
        self.markdown_parser = MarkdownParser()
        self.block_converter = BlockConverter()

    def sync_file_to_notion(self, file_path: str) -> Tuple[bool, str]:
        """
        Sync a markdown file to Notion.

        Args:
            file_path: Path to markdown file.

        Returns:
            Tuple of (success, message)
        """
        if not self.notion_client:
            return False, "Notion API token not configured"

        try:
            # Parse the markdown file
            metadata, html_content, raw_content = self.markdown_parser.parse_file(file_path)
            
            # Check if this file is already linked to a Notion page
            notion_page_id = metadata.get("notion_page_id")
            page_exists = False
            
            if notion_page_id:
                try:
                    # Try to fetch the page to see if it exists
                    self.notion_client.get_page(notion_page_id)
                    page_exists = True
                except Exception as e:
                    # Page doesn't exist or we don't have access
                    page_exists = False
            
            # Get or create title
            title = metadata.get("title")
            if not title:
                # Try to extract title from content
                title = self.markdown_parser.extract_title(raw_content)
                if not title:
                    # Use filename as fallback
                    title = os.path.splitext(os.path.basename(file_path))[0]
            
            # Convert markdown to Notion blocks
            blocks = self.block_converter.markdown_to_blocks(raw_content)
            
            if page_exists:
                # Update existing page
                self.notion_client.update_page_blocks(notion_page_id, blocks)
                message = f"Updated Notion page: {title}"
            else:
                # Create new page
                parent_id = self.config.get("notion.parent_page_id")
                if not parent_id:
                    return False, "Parent page ID not configured"
                    
                # Format parent_id with dashes if needed (sometimes Notion requires this format)
                if len(parent_id) == 32 and "-" not in parent_id:
                    parent_id = f"{parent_id[0:8]}-{parent_id[8:12]}-{parent_id[12:16]}-{parent_id[16:20]}-{parent_id[20:]}"
                
                # Determine if this is a database or page ID (this will be automatically handled by NotionClient)
                
                properties = {
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                }
                
                # Add any additional properties from metadata
                # But only if creating a database page - don't add properties to regular pages
                # as they may not be supported
                try:
                    # Try to determine if this is a database first
                    self.notion_client.client.databases.retrieve(database_id=parent_id)
                    
                    # If we get here, it's a database and we can add properties
                    for key, value in metadata.items():
                        if key not in ["title", "notion_page_id", "last_synced"]:
                            # Simple text property for now
                            properties[key] = {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": str(value)
                                        }
                                    }
                                ]
                            }
                except Exception:
                    # If it's not a database, only use the title property
                    pass
                
                # Create the page
                page = self.notion_client.create_page(parent_id, title, properties)
                notion_page_id = page["id"]
                
                # Add blocks to the page
                self.notion_client.update_page_blocks(notion_page_id, blocks)
                
                # Update the frontmatter with the new page ID
                self.markdown_parser.update_frontmatter(
                    file_path, 
                    {
                        "notion_page_id": notion_page_id,
                        "last_synced": datetime.now().isoformat()
                    }
                )
                
                message = f"Created new Notion page: {title}"
            
            # Update last_synced in frontmatter
            self.markdown_parser.update_frontmatter(
                file_path,
                {"last_synced": datetime.now().isoformat()}
            )
            
            return True, message
            
        except Exception as e:
            return False, f"Error syncing file to Notion: {str(e)}"

    def sync_notion_to_file(self, notion_page_id: str, file_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Sync a Notion page to a markdown file.

        Args:
            notion_page_id: Notion page ID.
            file_path: Path to markdown file. If None, a new file will be created.

        Returns:
            Tuple of (success, message)
        """
        if not self.notion_client:
            return False, "Notion API token not configured"

        try:
            # Get the page from Notion
            page = self.notion_client.get_page(notion_page_id)
            
            # Get page title
            title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
            
            # Get page blocks
            blocks = self.notion_client.get_page_blocks(notion_page_id)
            
            # Convert blocks to markdown
            markdown_content = self.block_converter.blocks_to_markdown(blocks)
            
            # Create metadata
            metadata = {
                "title": title,
                "notion_page_id": notion_page_id,
                "last_synced": datetime.now().isoformat()
            }
            
            # Extract other properties from the page
            for key, value in page.get("properties", {}).items():
                if key != "title":
                    # Try to extract simple text properties
                    if value.get("type") == "rich_text":
                        rich_text = value.get("rich_text", [])
                        if rich_text:
                            text_content = rich_text[0].get("text", {}).get("content", "")
                            metadata[key] = text_content
            
            if file_path:
                # Check if file exists
                if os.path.exists(file_path):
                    # Update existing file
                    self.markdown_parser.create_markdown_with_frontmatter(file_path, metadata, markdown_content)
                    message = f"Updated markdown file: {file_path}"
                else:
                    # Create new file
                    self.markdown_parser.create_markdown_with_frontmatter(file_path, metadata, markdown_content)
                    message = f"Created new markdown file: {file_path}"
            else:
                # Create new file in the configured markdown root directory
                markdown_root = self.config.get("directories.markdown_root", "./docs")
                os.makedirs(markdown_root, exist_ok=True)
                
                # Sanitize title for filename
                filename = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '' for c in title])
                filename = filename.replace(' ', '-').lower()
                
                file_path = os.path.join(markdown_root, f"{filename}.md")
                
                # Create new file
                self.markdown_parser.create_markdown_with_frontmatter(file_path, metadata, markdown_content)
                message = f"Created new markdown file: {file_path}"
                
            return True, message
            
        except Exception as e:
            return False, f"Error syncing Notion page to file: {str(e)}"

    def detect_conflicts(self, file_path: str, notion_page_id: str) -> bool:
        """
        Detect if there are conflicts between a file and a Notion page.

        Args:
            file_path: Path to markdown file.
            notion_page_id: Notion page ID.

        Returns:
            True if there are conflicts, False otherwise.
        """
        try:
            # Parse the markdown file
            metadata, _, _ = self.markdown_parser.parse_file(file_path)
            
            # Get last sync time
            last_synced = metadata.get("last_synced")
            if not last_synced:
                # Never synced before, so no conflicts
                return False
                
            last_synced_dt = datetime.fromisoformat(last_synced)
            
            # Get page from Notion
            page = self.notion_client.get_page(notion_page_id)
            
            # Get last edited time from Notion
            notion_last_edited = page.get("last_edited_time")
            notion_last_edited_dt = datetime.fromisoformat(notion_last_edited.replace("Z", "+00:00"))
            
            # Get file last modified time
            file_last_modified = os.path.getmtime(file_path)
            file_last_modified_dt = datetime.fromtimestamp(file_last_modified)
            
            # Check if both were modified since last sync
            notion_modified = notion_last_edited_dt > last_synced_dt
            file_modified = file_last_modified_dt > last_synced_dt
            
            return notion_modified and file_modified
            
        except Exception:
            # If we can't determine, assume there are conflicts
            return True