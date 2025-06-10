# Markdown-to-Notion Sync Bridge Implementation Plan

## 1. Project Structure & Setup

```
markdown-notion-sync/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── notion_client.py       # Notion API wrapper
│   ├── markdown_parser.py     # Markdown processing
│   ├── sync_engine.py         # Core sync logic
│   ├── file_watcher.py        # File system monitoring
│   ├── block_converter.py     # Markdown → Notion blocks
│   └── cli.py                 # Command line interface
├── config/
│   └── config.yaml            # User configuration
├── tests/
├── requirements.txt
└── README.md
```

## 2. Configuration System

### YAML Configuration (`config/config.yaml`)
```yaml
notion:
  token: "secret_xxxxx"
  database_id: "optional-for-index-tracking"
  
sync:
  direction: "bidirectional"  # unidirectional, bidirectional
  conflict_resolution: "manual"  # auto_notion, auto_markdown, manual
  
directories:
  markdown_root: "./docs"
  excluded_patterns: ["*.tmp", "node_modules/**"]
  
mapping:
  # File to Notion page mapping strategies
  strategy: "frontmatter"  # frontmatter, filename, database
  
logging:
  level: "INFO"
  file: "./logs/sync.log"
```

### Configuration Management (`src/config.py`)
- Load and validate YAML config
- Environment variable overrides
- Default fallbacks
- Config validation

## 3. Core Components

### A. Notion API Client (`src/notion_client.py`)

**Key Responsibilities:**
- Authenticate with Notion API
- CRUD operations for pages and blocks
- Rate limiting and retry logic
- Error handling and logging

**Methods:**
```python
class NotionClient:
    def get_page(self, page_id: str) -> dict
    def create_page(self, parent_id: str, title: str, blocks: list) -> dict
    def update_page_blocks(self, page_id: str, blocks: list) -> bool
    def search_pages(self, query: str) -> list
    def get_page_metadata(self, page_id: str) -> dict
```

### B. Markdown Parser (`src/markdown_parser.py`)

**Key Responsibilities:**
- Parse markdown files with frontmatter
- Extract metadata (title, tags, notion_id, etc.)
- Convert markdown AST to intermediate format
- Handle special markdown extensions

**Methods:**
```python
class MarkdownParser:
    def parse_file(self, file_path: str) -> MarkdownDocument
    def extract_frontmatter(self, content: str) -> dict
    def parse_markdown_ast(self, content: str) -> list
    def get_file_metadata(self, file_path: str) -> dict
```

### C. Block Converter (`src/block_converter.py`)

**Key Responsibilities:**
- Convert markdown AST to Notion blocks
- Handle complex elements (tables, code, lists)
- Preserve formatting and structure
- Reverse conversion (Notion → Markdown)

**Conversion Mapping:**
```python
MARKDOWN_TO_NOTION = {
    'heading': 'heading_1|heading_2|heading_3',
    'paragraph': 'paragraph',
    'code_block': 'code',
    'quote': 'quote',
    'list_item': 'bulleted_list_item|numbered_list_item',
    'table': 'table',
    'image': 'image',
    'link': 'bookmark'  # or embedded in text
}
```

### D. Sync Engine (`src/sync_engine.py`)

**Key Responsibilities:**
- Orchestrate sync operations
- Conflict detection and resolution
- Maintain sync state/metadata
- Handle partial syncs and retries

**Core Methods:**
```python
class SyncEngine:
    def sync_file_to_notion(self, file_path: str) -> SyncResult
    def sync_notion_to_file(self, page_id: str) -> SyncResult
    def detect_conflicts(self, file_path: str, page_id: str) -> ConflictInfo
    def resolve_conflict(self, conflict: ConflictInfo) -> Resolution
    def full_sync(self) -> SyncReport
```

### E. File Watcher (`src/file_watcher.py`)

**Key Responsibilities:**
- Monitor markdown directory for changes
- Debounce rapid file changes
- Queue sync operations
- Handle file operations (create, modify, delete, move)

**Implementation:**
```python
class FileWatcher:
    def start_watching(self, directory: str, callback: callable)
    def stop_watching(self)
    def handle_file_event(self, event: FileSystemEvent)
```

## 4. Data Models

### Markdown Document
```python
@dataclass
class MarkdownDocument:
    file_path: str
    title: str
    content: str
    frontmatter: dict
    last_modified: datetime
    notion_page_id: Optional[str] = None
    checksum: str = ""
```

### Sync Result
```python
@dataclass
class SyncResult:
    success: bool
    file_path: str
    notion_page_id: str
    operation: str  # 'create', 'update', 'delete'
    conflicts: List[ConflictInfo]
    error_message: Optional[str] = None
```

## 5. Mapping Strategies

### Strategy 1: Frontmatter-based
```yaml
---
title: "My Document"
notion_page_id: "abc123-def456-ghi789"
tags: ["project", "documentation"]
last_synced: "2025-06-09T10:30:00Z"
---
# Document content here...
```

### Strategy 2: Database Index
- Maintain a local SQLite database
- Track file → page_id mappings
- Store sync metadata and checksums
- Enable complex queries and reporting

### Strategy 3: Filename Convention
- Use filename patterns to determine Notion location
- Support nested folder → page hierarchy mapping
- Handle filename changes gracefully

## 6. Conflict Resolution

### Conflict Detection
- Compare file modification time vs Notion last_edited_time
- Use content checksums for change detection
- Track sync state in metadata

### Resolution Strategies
1. **Manual**: Present conflicts to user for resolution
2. **Auto-Notion**: Always prefer Notion version
3. **Auto-Markdown**: Always prefer markdown version
4. **Timestamp**: Use most recently modified version

### Conflict UI
```python
def handle_conflict(conflict: ConflictInfo) -> Resolution:
    print(f"Conflict detected for: {conflict.file_path}")
    print("1. Use Notion version")
    print("2. Use Markdown version")
    print("3. Show diff and merge manually")
    choice = input("Choose resolution: ")
    # Handle user choice
```

## 7. Implementation Phases

### Phase 1: Core Functionality (Week 1-2)
- Basic Notion API client
- Simple markdown parsing
- Unidirectional sync (Markdown → Notion)
- Frontmatter-based mapping
- CLI interface

### Phase 2: Enhanced Features (Week 3-4)
- Bidirectional sync
- File watching
- Conflict detection
- Database index for mapping
- Better error handling

### Phase 3: Polish & Advanced (Week 5-6)
- Complex markdown support (tables, nested lists)
- Batch operations
- Sync reporting and logging
- Configuration validation
- Tests and documentation

### Phase 4: Advanced Features (Future)
- Web UI for conflict resolution
- Plugin system for custom converters
- Integration with popular markdown editors
- Webhook support for real-time sync

## 8. Technical Considerations

### Rate Limiting
- Notion API: 3 requests per second
- Implement exponential backoff
- Queue operations during high activity

### Error Handling
- Network timeouts and retries
- Invalid markdown handling
- Notion API errors (permissions, limits)
- File system permission issues

### Performance
- Batch API operations where possible
- Incremental sync (only changed files)
- Async operations for file watching
- Caching for frequently accessed data

### Security
- Secure token storage
- Input validation and sanitization
- Safe file operations
- No sensitive data in logs

## 9. Testing Strategy

### Unit Tests
- Individual component testing
- Mock Notion API responses
- Markdown parsing edge cases
- Configuration validation

### Integration Tests
- End-to-end sync scenarios
- Real Notion API testing (with test workspace)
- File system operations
- Conflict resolution flows

### Test Data
- Sample markdown files with various formats
- Test Notion workspace with known structure
- Edge cases (empty files, malformed markdown)

## 10. Deployment & Distribution

### Package Structure
- PyPI package for easy installation
- Docker container for isolated environments
- Standalone executables for non-Python users

### Documentation
- README with quick start guide
- Configuration reference
- API documentation
- Troubleshooting guide
- Example workflows

### CLI Interface
```bash
# Initial setup
md-notion-sync init --config ./config.yaml

# One-time sync
md-notion-sync sync --direction markdown-to-notion

# Start file watcher
md-notion-sync watch --daemon

# Handle conflicts
md-notion-sync conflicts --resolve
```