# Notion Markdown Sync

A Python application that syncs markdown files with Notion pages, enabling seamless two-way synchronization between local markdown files and Notion workspace.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/notion-md-sync.git
cd notion-md-sync

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

You have two options to configure the application:

### Option 1: Environment Variables (Recommended)

Create a `.env` file in the project root with the following variables:

```
NOTION_TOKEN=your_integration_token
NOTION_PARENT_PAGE_ID=your_page_id
SYNC_DIRECTION=markdown_to_notion
```

### Option 2: Configuration File

Copy `config/config.example.yaml` to `config/config.yaml` and edit it:

```yaml
notion:
  token: "your_integration_token"     # Your Notion integration token (without "secret_" prefix)
  parent_page_id: "your_page_id"      # ID of the page where new pages will be created
```

**Note:** Environment variables take precedence over the configuration file.

### Setting up Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name it (e.g., "Markdown Sync")
4. Select the workspace where you want to use it
5. Set capabilities (Read & Write content is required)
6. Copy the "Internal Integration Token" to your config file

### Sharing a Notion Page with your Integration

#### Method 1: Manual Configuration
1. Go to the Notion page you want to use as a parent
2. Click "Share" in the top right corner
3. In the search field, type the name of your integration (e.g., "Markdown Sync")
4. Select your integration and click "Invite"
5. Copy the page ID from the URL (format: `https://www.notion.so/Your-Page-Title-PAGEID`)
   - The page ID is the last part of the URL, often a string of 32 characters with or without hyphens
   - Example: `7771ed7d89c54d62aad9758773a13598` or `7771ed7d-89c5-4d62-aad9-758773a13598`
6. Add this page ID to your config file

#### Method 2: Using the Verification Tool (Recommended)
1. Create a new page in Notion that you control (one you have permission to edit)
2. Copy the page ID from the URL (it's the 32-character string at the end)
3. Share this page with your integration:
   - Click "Share" in the top right corner
   - In the search field, type the name of your integration
   - Select your integration and click "Invite"
4. Run the verification tool with the database creation option:
   ```bash
   python -m notion_md_sync verify --create-test-page
   ```
5. When prompted, enter the page ID you copied
6. The tool will create a database within your page and add its ID to your configuration
7. This database will be used as the parent for all synced markdown files

## Usage

The tool supports both push (markdown → Notion) and pull (Notion → markdown) directions.

### Push (Markdown to Notion)

```bash
# Push a single markdown file to Notion
notion-md-sync sync --file path/to/markdown.md --direction push

# Push all markdown files to Notion
notion-md-sync sync-all --direction push

# Preview which files would be pushed without actually syncing
notion-md-sync sync-all --dry-run --direction push
```

### Pull (Notion to Markdown)

```bash
# Pull from Notion to a markdown file (requires existing file with notion_page_id in frontmatter)
notion-md-sync sync --file path/to/markdown.md --direction pull

# Pull all linked Notion pages to their corresponding markdown files
notion-md-sync sync-all --direction pull

# Discover and pull pages from your Notion workspace (recommended for new setups)
notion-md-sync pull-workspace

# Pull specific pages using search query
notion-md-sync pull-workspace --query "project notes"

# Preview what pages would be pulled without actually downloading them
notion-md-sync pull-workspace --dry-run

# Pull to a specific directory
notion-md-sync pull-workspace --directory ./my-notes

# Skip confirmation prompts (useful for automation)
notion-md-sync pull-workspace --yes

# Pull all child pages from a specific parent page (useful for organized hierarchies)
notion-md-sync pull-children --parent-id "your-parent-page-id"

# Preview child pages without pulling them
notion-md-sync pull-children --parent-id "your-parent-page-id" --dry-run

# Pull child pages to a specific directory
notion-md-sync pull-children --parent-id "your-parent-page-id" --directory ./my-notes --yes
```

### Other Commands

```bash
# Initialize configuration
notion-md-sync init --config config/config.yaml

# Verify Notion API connection and permissions
notion-md-sync verify

# Sync files from a specific directory
notion-md-sync sync-all --directory /path/to/my/notes

# Watch for changes and sync in real-time (in both directions)
notion-md-sync watch --direction both
```

## Features

- Bidirectional sync:
  - Push: Markdown → Notion
  - Pull: Notion → Markdown
- Workspace discovery: automatically find and pull pages from your Notion workspace
- Flexibility to sync individual files or entire directories
- Track relationships using YAML frontmatter
- Support for various markdown elements (headings, lists, code blocks, etc.)
- Search functionality for selective page pulling
- Configurable sync behavior
- Git integration for version control
- Real-time watching with selectable direction
- Dry-run mode for previewing changes

See the [ROADMAP.md](ROADMAP.md) file for planned features and enhancements.

## Development

```bash
# Run tests
pytest

# Run with debug logging
notion-md-sync --debug sync
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full list of planned features and enhancements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.