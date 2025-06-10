"""
Notion API client wrapper with additional functionality.
"""

import time
from typing import Dict, List, Any, Optional
from notion_client import Client


class NotionClient:
    """Wrapper around the official Notion API client with additional functionality."""

    def __init__(self, token: str):
        """
        Initialize Notion client.

        Args:
            token: Notion API token.
        """
        self.client = Client(auth=token)
        self.rate_limit_remaining = 1000
        self.rate_limit_reset_at = 0

    def _handle_rate_limits(self):
        """Handle rate limiting by waiting if necessary."""
        if self.rate_limit_remaining < 10:
            current_time = time.time()
            if current_time < self.rate_limit_reset_at:
                wait_time = self.rate_limit_reset_at - current_time + 1
                time.sleep(wait_time)

    def _update_rate_limits(self, response_headers: Dict[str, str]):
        """
        Update rate limit information from response headers.

        Args:
            response_headers: Response headers from Notion API.
        """
        if "x-ratelimit-remaining" in response_headers:
            self.rate_limit_remaining = int(response_headers["x-ratelimit-remaining"])
        
        if "x-ratelimit-reset-at" in response_headers:
            reset_time = response_headers["x-ratelimit-reset-at"]
            self.rate_limit_reset_at = time.mktime(time.strptime(reset_time, "%Y-%m-%dT%H:%M:%S.%fZ"))

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Get a page from Notion.

        Args:
            page_id: ID of the page to get.

        Returns:
            Page data.
        """
        self._handle_rate_limits()
        response = self.client.pages.retrieve(page_id=page_id)
        return response

    def get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Get all blocks for a page.

        Args:
            page_id: ID of the page to get blocks for.

        Returns:
            List of block data.
        """
        self._handle_rate_limits()
        blocks = []
        start_cursor = None
        
        while True:
            response = self.client.blocks.children.list(
                block_id=page_id,
                start_cursor=start_cursor
            )
            
            blocks.extend(response["results"])
            
            if not response.get("has_more", False):
                break
                
            start_cursor = response.get("next_cursor")
            self._handle_rate_limits()
            
        return blocks

    def create_page(self, parent_id: str, title: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new page in Notion.

        Args:
            parent_id: ID of the parent page or database.
            title: Title of the new page.
            properties: Additional properties for the page.

        Returns:
            Created page data.
        """
        self._handle_rate_limits()
        
        if not properties:
            properties = {}
            
        # First, try to determine if this is a database or page ID
        is_database = False
        
        try:
            # Try to retrieve as database first
            self.client.databases.retrieve(database_id=parent_id)
            is_database = True
            print(f"Identified {parent_id} as a database ID")
        except Exception:
            # If that fails, assume it's a page ID
            print(f"Assuming {parent_id} is a page ID")
        
        # Set up the parent reference based on what we determined
        if is_database:
            parent = {"type": "database_id", "database_id": parent_id}
            
            # For database parents, ensure title property exists with the right name
            # This can vary by database, so we'll retrieve the database to find the title property
            try:
                db = self.client.databases.retrieve(database_id=parent_id)
                title_property = None
                
                # Find the title property
                for prop_name, prop_details in db.get("properties", {}).items():
                    if prop_details.get("type") == "title":
                        title_property = prop_name
                        break
                
                if title_property and title_property not in properties:
                    properties[title_property] = {
                        "title": [{"type": "text", "text": {"content": title}}]
                    }
                    print(f"Using title property: {title_property}")
            except Exception as e:
                print(f"Error getting database structure: {str(e)}")
                # Fall back to "Title" as the property name
                if "Title" not in properties and "title" not in properties:
                    properties["Title"] = {
                        "title": [{"type": "text", "text": {"content": title}}]
                    }
        else:
            # For page parents
            parent = {"type": "page_id", "page_id": parent_id}
            
            # Set up the title property
            if "title" not in properties:
                properties["title"] = {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
        
        print(f"Creating page with parent: {parent}")
        print(f"Properties: {properties}")
        
        try:
            response = self.client.pages.create(parent=parent, properties=properties)
            return response
        except Exception as e:
            # If the first attempt fails, try the opposite parent type
            print(f"Error creating page: {str(e)}")
            
            if is_database:
                print("Trying as page instead...")
                parent = {"type": "page_id", "page_id": parent_id}
            else:
                print("Trying as database instead...")
                parent = {"type": "database_id", "database_id": parent_id}
                
                # For database parents, ensure title property exists
                if "Title" not in properties and "title" not in properties:
                    properties["Title"] = {
                        "title": [{"type": "text", "text": {"content": title}}]
                    }
            
            try:
                response = self.client.pages.create(parent=parent, properties=properties)
                return response
            except Exception as e2:
                error_msg = f"Failed to create page with both parent types. Original error: {str(e)}. Second error: {str(e2)}"
                print(error_msg)
                raise Exception(error_msg)

    def update_page_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update blocks on a page.

        Args:
            page_id: ID of the page to update.
            blocks: List of block data to add to the page.

        Returns:
            Updated list of blocks.
        """
        self._handle_rate_limits()
        
        # First, we'll clear existing blocks
        existing_blocks = self.get_page_blocks(page_id)
        for block in existing_blocks:
            self._handle_rate_limits()
            self.client.blocks.delete(block_id=block["id"])
            
        # Then add new blocks
        response = self.client.blocks.children.append(
            block_id=page_id,
            children=blocks
        )
        
        return response["results"]

    def search_pages(self, query: str = "", filter_pages: bool = True, filter_databases: bool = False) -> List[Dict[str, Any]]:
        """
        Search for pages in Notion workspace.

        Args:
            query: Search query. If empty, returns all accessible pages.
            filter_pages: Whether to include pages in results.
            filter_databases: Whether to include databases in results.

        Returns:
            List of page/database data.
        """
        self._handle_rate_limits()
        
        filter_conditions = {"value": "page" if filter_pages else "database", "property": "object"}
        
        if query:
            response = self.client.search(
                query=query,
                filter=filter_conditions
            )
        else:
            response = self.client.search(
                filter=filter_conditions
            )
        
        return response.get("results", [])

    def list_all_pages(self) -> List[Dict[str, Any]]:
        """
        List all accessible pages in the Notion workspace.

        Returns:
            List of page data.
        """
        return self.search_pages(query="", filter_pages=True, filter_databases=False)

    def get_child_pages(self, parent_page_id: str) -> List[Dict[str, Any]]:
        """
        Get all child pages of a specific parent page.

        Args:
            parent_page_id: ID of the parent page.

        Returns:
            List of child page data.
        """
        self._handle_rate_limits()
        
        # Get all blocks from the parent page
        blocks = self.get_page_blocks(parent_page_id)
        
        child_pages = []
        for block in blocks:
            # Check if block is a child page
            if block.get("type") == "child_page":
                child_page_id = block.get("id")
                if child_page_id:
                    try:
                        # Get the full page data
                        page_data = self.get_page(child_page_id)
                        child_pages.append(page_data)
                    except Exception as e:
                        print(f"Warning: Could not access child page {child_page_id}: {str(e)}")
                        continue
        
        return child_pages