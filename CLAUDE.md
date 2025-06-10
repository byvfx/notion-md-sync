# CLAUDE.md - Guidelines for notion-md-sync

## Commands
- Build: `npm run build`
- Dev: `npm run dev`
- Lint: `npm run lint`
- Test: `npm run test`
- Single test: `npm run test -- -t "test name"`
- Typecheck: `npm run typecheck`

## Code Style
- **Formatting**: Prettier with 2-space indentation
- **Imports**: Group and sort imports (external → internal)
- **Types**: TypeScript with strict mode enabled
- **Naming**: snake_case for variables/functions, PascalCase for classes/components
- **Error Handling**: Use try/catch with specific error types
- **Async**: Prefer async/await over raw promises
- **Documentation**: JSDoc for public API functions
- **Tests**: Jest with descriptive test names



# Markdown-to-Notion Sync Bridge

## Project Overview
Build a Python application that syncs markdown files with Notion pages, enabling seamless two-way synchronization between local markdown files and Notion workspace.

## Core Requirements

### Primary Goal
Create a bridge that monitors local markdown files and automatically syncs them with corresponding Notion pages, handling conflicts and maintaining consistency between both formats.

### Technical Stack
- **Language**: Python 3.9+
- **Key Libraries**: 
  - `notion-client` (official Notion API)
  - `watchdog` (file system monitoring)
  - `python-markdown` or `mistune` (markdown parsing)
  - `python-frontmatter` (YAML frontmatter handling)
  - `click` (CLI interface)
  - `pyyaml` (configuration)

## Architecture

### Project Structure
```
markdown-notion-sync/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── notion_client.py       # Notion API wrapper
│   ├── markdown_parser.py     # Markdown processing
│   ├── sync_engine.py         # Core sync logic
│   ├── block_converter.py     # Markdown ↔ Notion blocks
│   ├── file_watcher.py        # File system monitoring
│   └── cli.py                 # Command line interface
├── config/
│   └── config.yaml            # User configuration
├── tests/
├── requirements.txt
└── README.md
```

### Configuration System
Create a YAML-based configuration supporting:
- Notion API token and workspace settings
- Sync direction (unidirectional/bidirectional)
- File mapping strategies (frontmatter-based preferred)
- Conflict resolution preferences
- Directory monitoring settings

Example config structure:
```yaml
notion:
  token: "secret_xxxxx"
sync:
  direction: "bidirectional"
  conflict_resolution: "manual"
directories:
  markdown_root: "./docs"
  excluded_patterns: ["*.tmp", "node_modules/**"]
mapping:
  strategy: "frontmatter"
```

## Implementation Phases

### Phase 1: Foundation (Start Here)
1. **Project Setup**
   - Initialize Python project with proper structure
   - Set up requirements.txt with core dependencies
   - Create basic configuration loading system

2. **Notion API Client**
   - Implement authenticated Notion API wrapper
   - Add methods for: get_page, create_page, update_page_blocks
   - Include rate limiting and error handling

3. **Markdown Parser**
   - Parse markdown files with frontmatter support
   - Extract metadata (title, notion_page_id from frontmatter)
   - Convert markdown to intermediate representation

4. **Basic Sync (Unidirectional)**
   - Implement markdown → Notion sync only
   - Use frontmatter to track page mappings
   - Handle basic markdown elements (headers, paragraphs, lists)

### Phase 2: Enhanced Features
1. **Block Converter**
   - Convert markdown AST to Notion block format
   - Handle complex elements: tables, code blocks, nested lists
   - Implement reverse conversion (Notion → markdown)

2. **File Watcher**
   - Monitor markdown directory for changes
   - Debounce rapid changes
   - Queue sync operations

3. **Conflict Resolution**
   - Detect conflicts using timestamps and checksums
   - Implement manual conflict resolution UI
   - Add automatic resolution strategies

### Phase 3: Polish
1. **CLI Interface**
   - Commands: init, sync, watch, conflicts
   - Progress indicators and logging
   - Configuration validation

2. **Error Handling & Testing**
   - Comprehensive error handling
   - Unit and integration tests
   - Documentation and examples

## Key Technical Details

### Frontmatter Mapping Strategy
Use YAML frontmatter in markdown files to track Notion page relationships:
```markdown
---
title: "Document Title"
notion_page_id: "abc123-def456-ghi789"
last_synced: "2025-06-09T10:30:00Z"
tags: ["project", "docs"]
---

# Document content here...
```

### Block Conversion Mapping
```python
MARKDOWN_TO_NOTION = {
    'heading': 'heading_1|heading_2|heading_3',
    'paragraph': 'paragraph',
    'code_block': 'code',
    'quote': 'quote',
    'list_item': 'bulleted_list_item|numbered_list_item',
    'table': 'table',
    'image': 'image'
}
```

### Core Classes Needed
```python
class NotionClient:
    # Notion API operations with rate limiting
    
class MarkdownParser:
    # Parse files, extract frontmatter, convert to AST
    
class BlockConverter:
    # Convert between markdown and Notion block formats
    
class SyncEngine:
    # Orchestrate sync operations and conflict resolution
    
class FileWatcher:
    # Monitor filesystem and trigger syncs
```

## Development Priorities

### Must-Have Features
- ✅ Notion API authentication and basic operations
- ✅ Markdown file parsing with frontmatter
- ✅ Unidirectional sync (markdown → Notion)
- ✅ Basic conflict detection
- ✅ CLI interface for manual operations

### Nice-to-Have Features
- 🔄 Bidirectional sync
- 👀 Real-time file watching
- 🔀 Advanced conflict resolution
- 📊 Sync reporting and logging
- 🎨 Rich markdown formatting support

### Future Enhancements
- 🌐 Web UI for conflict resolution
- 🔌 Plugin system for custom converters
- 📱 Integration with markdown editors
- 🔗 Webhook support for real-time sync

## Testing Strategy
- Unit tests for each component
- Integration tests with mock Notion API
- End-to-end tests with test workspace
- Edge case handling (empty files, malformed markdown)

## Security Considerations
- Secure token storage (environment variables)
- Input validation and sanitization
- Safe file operations
- No sensitive data in logs

## Getting Started Commands
```bash
# Initialize project
python -m pip install -r requirements.txt

# Setup configuration
python -m src.cli init --config config/config.yaml

# Test basic sync
python -m src.cli sync --file path/to/test.md

# Start file watcher (when implemented)
python -m src.cli watch --daemon
```

Start with Phase 1 and build incrementally. Focus on getting basic markdown → Notion sync working first, then add complexity gradually.