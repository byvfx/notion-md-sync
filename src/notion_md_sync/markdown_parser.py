"""
Markdown parser with frontmatter support.
"""

import os
from typing import Dict, Any, Tuple, Optional, List
import frontmatter
import markdown
from markdown.extensions.toc import TocExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension


class MarkdownParser:
    """Parser for markdown files with frontmatter."""

    def __init__(self):
        """Initialize the markdown parser with extensions."""
        self.md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            FencedCodeExtension(),
            TableExtension(),
            TocExtension(permalink=True)
        ])

    def parse_file(self, file_path: str) -> Tuple[Dict[str, Any], str, str]:
        """
        Parse a markdown file, extracting frontmatter and content.

        Args:
            file_path: Path to markdown file.

        Returns:
            Tuple of (frontmatter, html_content, raw_content)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            
        # Extract frontmatter
        metadata = post.metadata
        
        # Get raw content
        raw_content = post.content
        
        # Convert to HTML
        self.md.reset()
        html_content = self.md.convert(raw_content)
        
        return metadata, html_content, raw_content

    def update_frontmatter(self, file_path: str, new_metadata: Dict[str, Any]) -> None:
        """
        Update frontmatter in a markdown file.

        Args:
            file_path: Path to markdown file.
            new_metadata: New metadata to update.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            
        # Update metadata
        for key, value in new_metadata.items():
            post[key] = value
            
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def create_markdown_with_frontmatter(self, file_path: str, metadata: Dict[str, Any], content: str) -> None:
        """
        Create a new markdown file with frontmatter.

        Args:
            file_path: Path to create the markdown file.
            metadata: Frontmatter metadata.
            content: Markdown content.
        """
        post = frontmatter.Post(content, **metadata)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

    def extract_title(self, content: str) -> Optional[str]:
        """
        Extract title from markdown content (first h1).

        Args:
            content: Markdown content.

        Returns:
            Title or None if not found.
        """
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return None

    def extract_headings(self, content: str) -> List[Tuple[int, str]]:
        """
        Extract all headings from markdown content.

        Args:
            content: Markdown content.

        Returns:
            List of tuples (level, heading_text).
        """
        lines = content.split('\n')
        headings = []
        
        for line in lines:
            if line.startswith('#'):
                # Count the number of # characters at the start
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break
                        
                text = line[level:].strip()
                headings.append((level, text))
                
        return headings