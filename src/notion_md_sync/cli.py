"""
Command-line interface for Notion Markdown Sync.
"""

import click
import os
import sys
from .config import Config


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logging")
@click.option("--config", default=None, help="Path to config file")
@click.pass_context
def cli(ctx, debug, config):
    """Notion Markdown Sync - Bridge between markdown files and Notion pages."""
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug
    ctx.obj["CONFIG"] = Config(config)


@cli.command()
@click.option("--config", default=None, help="Path to config file to create")
@click.pass_context
def init(ctx, config):
    """Initialize configuration file."""
    config_obj = ctx.obj["CONFIG"]
    if config:
        config_obj.config_path = config

    if os.path.exists(config_obj.config_path):
        if not click.confirm(f"Config file {config_obj.config_path} already exists. Overwrite?"):
            return

    # Create basic config structure
    config_obj.set("notion.token", "")
    config_obj.set("notion.parent_page_id", "")
    config_obj.set("sync.direction", "markdown_to_notion")
    config_obj.set("sync.conflict_resolution", "newer")
    config_obj.set("directories.markdown_root", "./docs")
    config_obj.set("directories.excluded_patterns", ["*.tmp", "node_modules/**"])
    config_obj.set("mapping.strategy", "frontmatter")

    config_obj.save()
    click.echo(f"Created configuration file at {config_obj.config_path}")
    click.echo("Edit this file to set your Notion API token and sync preferences.")


@cli.command()
@click.option("--file", required=True, help="Markdown file to sync")
@click.option("--direction", type=click.Choice(['push', 'pull']), default='push',
              help="Sync direction: push (markdown to Notion) or pull (Notion to markdown)")
@click.pass_context
def sync(ctx, file, direction):
    """Sync a single file between markdown and Notion."""
    config = ctx.obj["CONFIG"]
    
    # Validate configuration
    if not config.get("notion.token"):
        click.echo("Error: Notion API token not set in config. Please add your token to config/config.yaml.")
        sys.exit(1)
        
    if not config.get("notion.parent_page_id"):
        click.echo("Error: Notion parent page ID not set in config. Please add a page ID to config/config.yaml.")
        click.echo("Tip: Share a Notion page with your integration and use its ID.")
        sys.exit(1)

    if not config.validate():
        click.echo("Invalid configuration. Please check your config/config.yaml file.")
        sys.exit(1)

    if not os.path.exists(file):
        click.echo(f"Error: File {file} does not exist.")
        sys.exit(1)
    
    # Initialize sync engine
    from .sync_engine import SyncEngine
    sync_engine = SyncEngine(config)
    
    # Perform the sync based on direction
    if direction == 'push':
        click.echo(f"Pushing {file} to Notion...")
        success, message = sync_engine.sync_file_to_notion(file)
    else:  # pull
        # For pull, we need to get the Notion page ID from the frontmatter
        from .markdown_parser import MarkdownParser
        
        if not os.path.exists(file) or not os.path.isfile(file):
            # For pull, if the file doesn't exist, we'll create it
            if not click.confirm(f"File {file} doesn't exist. Create it?"):
                click.echo("Sync cancelled.")
                return
                
            # Get notion_page_id from command line if the file doesn't exist
            notion_page_id = click.prompt("Enter the Notion page ID to pull from", type=str)
            click.echo(f"Pulling from Notion page {notion_page_id} to {file}...")
            success, message = sync_engine.sync_notion_to_file(notion_page_id, file)
        else:
            # File exists, try to get notion_page_id from frontmatter
            try:
                parser = MarkdownParser()
                metadata, _, _ = parser.parse_file(file)
                notion_page_id = metadata.get("notion_page_id")
                
                if not notion_page_id:
                    notion_page_id = click.prompt("Notion page ID not found in frontmatter. Enter Notion page ID", type=str)
                
                click.echo(f"Pulling from Notion page {notion_page_id} to {file}...")
                success, message = sync_engine.sync_notion_to_file(notion_page_id, file)
            except Exception as e:
                click.echo(f"Error reading file: {str(e)}")
                sys.exit(1)
    
    if success:
        click.echo(f"Success: {message}")
    else:
        click.echo(f"Error: {message}")
        sys.exit(1)


@cli.command()
@click.option("--query", default="", help="Search query for Notion pages (empty = all accessible pages)")
@click.option("--directory", default=None, help="Directory to save pulled markdown files")
@click.option("--dry-run", is_flag=True, help="Show pages that would be pulled without actually pulling")
@click.option("--yes", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def pull_workspace(ctx, query, directory, dry_run, yes):
    """Discover and pull pages from Notion workspace."""
    config = ctx.obj['CONFIG']
    
    # Initialize sync engine
    from .sync_engine import SyncEngine
    sync_engine = SyncEngine(config)
    
    # Set directory for pulled files
    if directory:
        pull_directory = directory
    else:
        pull_directory = config.get("directories.markdown_root", "./docs")
    
    os.makedirs(pull_directory, exist_ok=True)
    
    try:
        # Search for pages in Notion workspace
        pages = sync_engine.notion_client.search_pages(query=query, filter_pages=True, filter_databases=False)
        
        if not pages:
            click.echo("No pages found in your Notion workspace.")
            if query:
                click.echo(f"Try removing the search query '{query}' to see all accessible pages.")
            return
        
        click.echo(f"Found {len(pages)} page(s) in your Notion workspace:")
        
        if dry_run:
            click.echo("Dry run - the following pages would be pulled:")
            for page in pages:
                title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
                page_id = page.get("id", "")
                click.echo(f"  {title} (ID: {page_id})")
            return
        
        # Confirm with user
        if not yes and not click.confirm(f"Pull {len(pages)} page(s) from Notion to {pull_directory}?"):
            click.echo("Pull cancelled.")
            return
        
        # Pull each page
        success_count = 0
        failure_count = 0
        
        with click.progressbar(pages, label="Pulling pages from Notion") as page_list:
            for page in page_list:
                page_id = page.get("id", "")
                title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
                
                # Create filename from title
                filename = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '' for c in title])
                filename = filename.replace(' ', '-').lower()
                if not filename:
                    filename = f"untitled-{page_id[:8]}"
                
                file_path = os.path.join(pull_directory, f"{filename}.md")
                
                # Handle duplicate filenames
                counter = 1
                original_file_path = file_path
                while os.path.exists(file_path):
                    name, ext = os.path.splitext(original_file_path)
                    file_path = f"{name}-{counter}{ext}"
                    counter += 1
                
                try:
                    success, message = sync_engine.sync_notion_to_file(page_id, file_path)
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        click.echo(f"\nFailed to pull '{title}': {message}")
                except Exception as e:
                    failure_count += 1
                    click.echo(f"\nError pulling '{title}': {str(e)}")
        
        # Show results
        click.echo(f"\nPull completed:")
        click.echo(f"  Successfully pulled: {success_count}")
        click.echo(f"  Failed: {failure_count}")
        click.echo(f"  Files saved to: {pull_directory}")
        
    except Exception as e:
        click.echo(f"Error searching Notion workspace: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--parent-id", required=True, help="Notion page ID to pull child pages from")
@click.option("--directory", default=None, help="Directory to save pulled markdown files")
@click.option("--dry-run", is_flag=True, help="Show pages that would be pulled without actually pulling")
@click.option("--yes", is_flag=True, help="Skip confirmation prompts")
@click.pass_context
def pull_children(ctx, parent_id, directory, dry_run, yes):
    """Pull all child pages from a specific Notion parent page."""
    config = ctx.obj['CONFIG']
    
    # Initialize sync engine
    from .sync_engine import SyncEngine
    sync_engine = SyncEngine(config)
    
    # Set directory for pulled files
    if directory:
        pull_directory = directory
    else:
        pull_directory = config.get("directories.markdown_root", "./docs")
    
    os.makedirs(pull_directory, exist_ok=True)
    
    try:
        # First get the parent page to show its title
        try:
            parent_page = sync_engine.notion_client.get_page(parent_id)
            parent_title = parent_page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", "Unknown")
            click.echo(f"Getting child pages from: {parent_title}")
        except Exception as e:
            click.echo(f"Warning: Could not access parent page {parent_id}: {str(e)}")
            parent_title = "Unknown"
        
        # Get child pages
        child_pages = sync_engine.notion_client.get_child_pages(parent_id)
        
        if not child_pages:
            click.echo(f"No child pages found under '{parent_title}'.")
            return
        
        click.echo(f"Found {len(child_pages)} child page(s):")
        
        if dry_run:
            click.echo("Dry run - the following child pages would be pulled:")
            for page in child_pages:
                title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
                page_id = page.get("id", "")
                click.echo(f"  {title} (ID: {page_id})")
            return
        
        # Confirm with user
        if not yes and not click.confirm(f"Pull {len(child_pages)} child page(s) from '{parent_title}' to {pull_directory}?"):
            click.echo("Pull cancelled.")
            return
        
        # Pull each child page
        success_count = 0
        failure_count = 0
        
        with click.progressbar(child_pages, label="Pulling child pages from Notion") as page_list:
            for page in page_list:
                page_id = page.get("id", "")
                title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("text", {}).get("content", "Untitled")
                
                # Create filename from title
                filename = "".join([c if c.isalnum() or c in [' ', '-', '_'] else '' for c in title])
                filename = filename.replace(' ', '-').lower()
                if not filename:
                    filename = f"untitled-{page_id[:8]}"
                
                file_path = os.path.join(pull_directory, f"{filename}.md")
                
                # Handle duplicate filenames
                counter = 1
                original_file_path = file_path
                while os.path.exists(file_path):
                    name, ext = os.path.splitext(original_file_path)
                    file_path = f"{name}-{counter}{ext}"
                    counter += 1
                
                try:
                    success, message = sync_engine.sync_notion_to_file(page_id, file_path)
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        click.echo(f"\nFailed to pull '{title}': {message}")
                except Exception as e:
                    failure_count += 1
                    click.echo(f"\nError pulling '{title}': {str(e)}")
        
        # Show results
        click.echo(f"\nPull completed:")
        click.echo(f"  Successfully pulled: {success_count}")
        click.echo(f"  Failed: {failure_count}")
        click.echo(f"  Files saved to: {pull_directory}")
        
    except Exception as e:
        click.echo(f"Error getting child pages: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--directory", default=None, help="Directory containing markdown files to sync (defaults to config's markdown_root)")
@click.option("--dry-run", is_flag=True, help="Show files that would be synced without actually syncing")
@click.option("--direction", type=click.Choice(['push', 'pull']), default='push',
              help="Sync direction: push (markdown to Notion) or pull (Notion to markdown)")
@click.pass_context
def sync_all(ctx, directory, dry_run, direction):
    """Sync all markdown files with Notion (recommended)."""
    config = ctx.obj["CONFIG"]
    
    # Validate configuration
    if not config.get("notion.token"):
        click.echo("Error: Notion API token not set in config. Please add your token to config/config.yaml.")
        sys.exit(1)
        
    if not config.get("notion.parent_page_id"):
        click.echo("Error: Notion parent page ID not set in config. Please add a page ID to config/config.yaml.")
        click.echo("Tip: Share a Notion page with your integration and use its ID.")
        sys.exit(1)

    if not config.validate():
        click.echo("Invalid configuration. Please check your config/config.yaml file.")
        sys.exit(1)
    
    # Get the directory to sync
    markdown_dir = directory or config.get("directories.markdown_root", "./docs")
    
    if not os.path.exists(markdown_dir):
        click.echo(f"Error: Directory {markdown_dir} does not exist.")
        sys.exit(1)
    
    # Initialize sync engine
    from .sync_engine import SyncEngine
    sync_engine = SyncEngine(config)
    
    # Find all markdown files in the directory
    markdown_files = []
    for root, _, files in os.walk(markdown_dir):
        for file in files:
            if file.lower().endswith(('.md', '.markdown')):
                markdown_files.append(os.path.join(root, file))
    
    if not markdown_files:
        click.echo(f"No markdown files found in {markdown_dir}")
        sys.exit(0)
    
    # Display summary
    click.echo(f"Found {len(markdown_files)} markdown files in {markdown_dir}")
    
    # Display action based on direction
    action = "Pushing to" if direction == "push" else "Pulling from"
    
    # In dry run mode with different message based on direction
    if dry_run:
        click.echo(f"Dry run - the following files would be {action.lower()} Notion:")
        for file in markdown_files:
            click.echo(f"  {file}")
        return
    
    # Confirm with user
    if not click.confirm(f"{action} Notion for {len(markdown_files)} files?"):
        click.echo("Sync cancelled.")
        return
    
    # Perform the sync
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    with click.progressbar(markdown_files, label=f"{action} Notion") as files:
        for file in files:
            try:
                if direction == "push":
                    success, message = sync_engine.sync_file_to_notion(file)
                else:  # pull
                    # Get notion_page_id from frontmatter
                    try:
                        from .markdown_parser import MarkdownParser
                        parser = MarkdownParser()
                        
                        if os.path.exists(file):
                            metadata, _, _ = parser.parse_file(file)
                            notion_page_id = metadata.get("notion_page_id")
                            
                            if notion_page_id:
                                success, message = sync_engine.sync_notion_to_file(notion_page_id, file)
                                if success:
                                    success_count += 1
                                else:
                                    failure_count += 1
                                    click.echo(f"\nFailed to pull {file}: {message}")
                            else:
                                # Skip files without notion_page_id when pulling
                                skipped_count += 1
                                click.echo(f"\nSkipped {file}: No notion_page_id in frontmatter")
                        else:
                            # Skip files that don't exist when pulling
                            skipped_count += 1
                    except Exception as e:
                        failure_count += 1
                        click.echo(f"\nError reading {file}: {str(e)}")
                        continue
                
                if direction == "push" and success:
                    success_count += 1
                elif direction == "push" and not success:
                    failure_count += 1
                    click.echo(f"\nFailed to push {file}: {message}")
            except Exception as e:
                failure_count += 1
                click.echo(f"\nError syncing {file}: {str(e)}")
    
    # Display summary
    click.echo(f"\nSync complete: {success_count} succeeded, {failure_count} failed, {skipped_count} skipped")


@cli.command()
@click.option("--daemon/--no-daemon", default=False, help="Run as a daemon")
@click.option("--direction", type=click.Choice(['push', 'pull', 'both']), default='push',
              help="Sync direction: push (markdown to Notion), pull (Notion to markdown), or both")
@click.pass_context
def watch(ctx, daemon, direction):
    """Watch for changes and sync automatically in the specified direction."""
    config = ctx.obj["CONFIG"]
    if not config.validate():
        click.echo("Invalid configuration. Please run init and set your Notion API token.")
        sys.exit(1)

    # Initialize sync engine
    from .sync_engine import SyncEngine
    sync_engine = SyncEngine(config)
    
    # Define callback for file changes based on direction
    def on_file_change(file_path):
        click.echo(f"File changed: {file_path}")
        
        if direction in ['push', 'both']:
            # Sync from markdown to Notion
            click.echo(f"Pushing {file_path} to Notion...")
            success, message = sync_engine.sync_file_to_notion(file_path)
            if success:
                click.echo(f"Push succeeded: {message}")
            else:
                click.echo(f"Push failed: {message}")
        
        if direction in ['pull', 'both']:
            # For pull, we need the notion_page_id from frontmatter
            try:
                from .markdown_parser import MarkdownParser
                parser = MarkdownParser()
                
                if os.path.exists(file_path):
                    metadata, _, _ = parser.parse_file(file_path)
                    notion_page_id = metadata.get("notion_page_id")
                    
                    if notion_page_id:
                        click.echo(f"Pulling from Notion page {notion_page_id} to {file_path}...")
                        success, message = sync_engine.sync_notion_to_file(notion_page_id, file_path)
                        if success:
                            click.echo(f"Pull succeeded: {message}")
                        else:
                            click.echo(f"Pull failed: {message}")
                    else:
                        click.echo(f"Skipped pulling: No notion_page_id in frontmatter for {file_path}")
                else:
                    click.echo(f"Skipped pulling: File {file_path} does not exist")
            except Exception as e:
                click.echo(f"Error during pull: {str(e)}")
    
    # Initialize file watcher
    from .file_watcher import FileWatcher
    watch_dir = config.get("directories.markdown_root", "./docs")
    
    direction_text = "both directions" if direction == "both" else f"{direction} direction"
    click.echo(f"Starting file watcher for directory: {watch_dir} in {direction_text}")
    click.echo("Press Ctrl+C to stop")
    
    # Create and start the watcher
    watcher = FileWatcher(config, on_file_change)
    watcher.start(daemon=daemon)


@cli.command()
@click.option("--create-test-page", is_flag=True, help="Create a test page in the workspace root")
@click.pass_context
def verify(ctx, create_test_page):
    """Verify Notion API connection and page access."""
    config = ctx.obj["CONFIG"]
    
    # Check if token is set
    token = config.get("notion.token")
    if not token:
        click.echo("Error: Notion API token not set in config.")
        click.echo("Please add your integration token to config/config.yaml.")
        sys.exit(1)
        
    # Check if parent page ID is set
    parent_id = config.get("notion.parent_page_id")
    if not parent_id:
        click.echo("Error: Notion parent page ID not set in config.")
        click.echo("Please add a page ID to config/config.yaml.")
        sys.exit(1)
    
    click.echo("Verifying Notion API connection...")
    
    # Format parent_id with dashes if needed
    if len(parent_id) == 32 and "-" not in parent_id:
        formatted_id = f"{parent_id[0:8]}-{parent_id[8:12]}-{parent_id[12:16]}-{parent_id[16:20]}-{parent_id[20:]}"
        click.echo(f"Formatted page ID: {formatted_id}")
    else:
        formatted_id = parent_id
        
    # Try to access the API
    from notion_client import Client
    from notion_client.errors import APIResponseError
    
    try:
        client = Client(auth=token)
        
        # Test basic API access
        user = client.users.me()
        click.echo(f"✅ Connected to Notion API as {user.get('name', 'Unknown User')}")
        
        # Try to access the parent page
        parent_page_accessible = False
        click.echo(f"Checking access to parent page {formatted_id}...")
        try:
            page = client.pages.retrieve(page_id=formatted_id)
            click.echo(f"✅ Successfully accessed parent page: {page.get('url', 'Unknown URL')}")
            parent_page_accessible = True
            
            # Show page title if available
            if 'properties' in page and 'title' in page['properties']:
                title_obj = page['properties']['title']
                if 'title' in title_obj and title_obj['title']:
                    title = title_obj['title'][0]['plain_text'] if title_obj['title'] else "Untitled"
                    click.echo(f"   Page title: {title}")
                    
        except APIResponseError as e:
            error_msg = str(e)
            click.echo(f"❌ Could not access parent page: {error_msg}")
            click.echo("\nTroubleshooting steps:")
            click.echo("1. Verify the page ID is correct")
            click.echo("2. Make sure you've shared the page with your integration:")
            click.echo("   a. Open the page in Notion")
            click.echo("   b. Click 'Share' in the top right")
            click.echo("   c. Add your integration to the share list")
            
            # Only exit early if we're not creating a test page
            if not create_test_page:
                sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Failed to connect to Notion API: {str(e)}")
        click.echo("\nTroubleshooting steps:")
        click.echo("1. Check that your integration token is correct")
        click.echo("2. Verify your internet connection")
        sys.exit(1)
        
    # Try creating a test database if requested
    if create_test_page:
        click.echo("\nAttempting to create a test database...")
        click.echo("NOTE: To use this feature, you must first:")
        click.echo("1. Create a page in Notion that you control")
        click.echo("2. Share that page with your integration")
        click.echo("3. Use the page ID as a temporary parent")
        
        temp_parent_id = click.prompt("Enter ID of a page you've shared with the integration", default="")
        
        if not temp_parent_id:
            click.echo("No page ID provided. Skipping test database creation.")
        else:
            try:
                # Format the temp parent ID if needed
                if len(temp_parent_id) == 32 and "-" not in temp_parent_id:
                    temp_parent_id = f"{temp_parent_id[0:8]}-{temp_parent_id[8:12]}-{temp_parent_id[12:16]}-{temp_parent_id[16:20]}-{temp_parent_id[20:]}"
                    
                click.echo(f"Using parent page ID: {temp_parent_id}")
                    
                # Create a database as a child of the temporary parent page
                test_db = client.databases.create(
                    parent={"type": "page_id", "page_id": temp_parent_id},
                    title=[
                        {
                            "type": "text",
                            "text": {
                                "content": "Markdown Sync Database"
                            }
                        }
                    ],
                    properties={
                        "Title": {
                            "title": {}
                        },
                        "Tags": {
                            "multi_select": {}
                        },
                        "Last Synced": {
                            "date": {}
                        }
                    }
                )
                
                db_id = test_db["id"]
                db_url = test_db.get("url", "Unknown URL")
                
                click.echo(f"✅ Created test database with ID: {db_id}")
                click.echo(f"   URL: {db_url}")
                click.echo(f"   Use this ID in your config file as the parent_page_id")
                
                # Update the config with the new database ID
                if click.confirm("Update your config with this new database ID?"):
                    config.set("notion.parent_page_id", db_id)
                    config.save()
                    click.echo("✅ Configuration updated with new database ID")
                    
            except Exception as e:
                click.echo(f"❌ Failed to create test database: {str(e)}")
                click.echo("Make sure the page ID is correct and the page is shared with your integration.")
    
    click.echo("\n✅ Notion setup verified successfully!")


def main():
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()