"""
Converter between Markdown elements and Notion blocks.
"""

from typing import Dict, List, Any, Tuple
import re


class BlockConverter:
    """Converter between markdown elements and Notion blocks."""

    # Mapping from markdown elements to Notion block types
    MARKDOWN_TO_NOTION = {
        'heading': ['heading_1', 'heading_2', 'heading_3'],
        'paragraph': 'paragraph',
        'code_block': 'code',
        'quote': 'quote',
        'bulleted_list': 'bulleted_list_item',
        'numbered_list': 'numbered_list_item',
        'table': 'table',
        'image': 'image',
    }

    def __init__(self):
        """Initialize the block converter."""
        pass

    def markdown_to_blocks(self, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Convert markdown content to Notion blocks.

        Args:
            markdown_content: Raw markdown content.

        Returns:
            List of Notion block objects.
        """
        # This is a simplified implementation that handles basic elements
        # A full implementation would need to parse the markdown AST
        blocks = []
        lines = markdown_content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Headings
            heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                blocks.append(self._create_heading_block(text, level))
                i += 1
                continue
                
            # Code blocks
            if line.startswith('```'):
                language = line[3:].strip()
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                # Skip closing ```
                i += 1
                blocks.append(self._create_code_block('\n'.join(code_lines), language))
                continue
                
            # Bullet lists
            if line.startswith('- ') or line.startswith('* '):
                text = line[2:].strip()
                blocks.append(self._create_bullet_list_item(text))
                i += 1
                continue
                
            # Numbered lists
            numbered_match = re.match(r'^\d+\.\s+(.+)$', line)
            if numbered_match:
                text = numbered_match.group(1)
                blocks.append(self._create_numbered_list_item(text))
                i += 1
                continue
                
            # Quotes
            if line.startswith('> '):
                text = line[2:].strip()
                blocks.append(self._create_quote_block(text))
                i += 1
                continue
                
            # Paragraphs (default)
            blocks.append(self._create_paragraph_block(line))
            i += 1
                
        return blocks

    def blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Convert Notion blocks to markdown content.

        Args:
            blocks: List of Notion block objects.

        Returns:
            Markdown content.
        """
        # This is a simplified implementation
        markdown_lines = []
        
        for block in blocks:
            block_type = block.get('type')
            
            if block_type in ['heading_1', 'heading_2', 'heading_3']:
                level = int(block_type[-1])
                text = self._get_text_from_rich_text(block[block_type].get('rich_text', []))
                markdown_lines.append(f"{'#' * level} {text}")
                
            elif block_type == 'paragraph':
                text = self._get_text_from_rich_text(block['paragraph'].get('rich_text', []))
                markdown_lines.append(text)
                
            elif block_type == 'code':
                text = self._get_text_from_rich_text(block['code'].get('rich_text', []))
                language = block['code'].get('language', '')
                markdown_lines.append(f"```{language}")
                markdown_lines.append(text)
                markdown_lines.append("```")
                
            elif block_type == 'quote':
                text = self._get_text_from_rich_text(block['quote'].get('rich_text', []))
                markdown_lines.append(f"> {text}")
                
            elif block_type == 'bulleted_list_item':
                text = self._get_text_from_rich_text(block['bulleted_list_item'].get('rich_text', []))
                markdown_lines.append(f"- {text}")
                
            elif block_type == 'numbered_list_item':
                text = self._get_text_from_rich_text(block['numbered_list_item'].get('rich_text', []))
                markdown_lines.append(f"1. {text}")
                
            # Add a blank line after each block
            markdown_lines.append("")
            
        return '\n'.join(markdown_lines)

    def _create_heading_block(self, text: str, level: int) -> Dict[str, Any]:
        """Create a heading block."""
        if level > 3:
            level = 3  # Notion only supports h1-h3
        block_type = f"heading_{level}"
        return {
            "type": block_type,
            block_type: {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }

    def _create_paragraph_block(self, text: str) -> Dict[str, Any]:
        """Create a paragraph block."""
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }

    def _create_code_block(self, code: str, language: str = "") -> Dict[str, Any]:
        """Create a code block."""
        return {
            "type": "code",
            "code": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": code
                        }
                    }
                ],
                "language": language
            }
        }

    def _create_quote_block(self, text: str) -> Dict[str, Any]:
        """Create a quote block."""
        return {
            "type": "quote",
            "quote": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }

    def _create_bullet_list_item(self, text: str) -> Dict[str, Any]:
        """Create a bulleted list item."""
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }

    def _create_numbered_list_item(self, text: str) -> Dict[str, Any]:
        """Create a numbered list item."""
        return {
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": text
                        }
                    }
                ]
            }
        }

    def _get_text_from_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract plain text from rich text array."""
        return ''.join(item.get('text', {}).get('content', '') for item in rich_text)