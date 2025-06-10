"""
File system watcher for monitoring markdown file changes.
"""

import os
import time
from typing import Callable, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from .config import Config


class MarkdownFileEventHandler(FileSystemEventHandler):
    """
    Event handler for markdown file changes.
    """

    def __init__(self, callback: Callable[[str], None], config: Config):
        """
        Initialize the event handler.

        Args:
            callback: Function to call when a markdown file is changed.
            config: Application configuration.
        """
        self.callback = callback
        self.config = config
        self.excluded_patterns = config.get("directories.excluded_patterns", [])
        self._last_events = {}  # For debouncing
        self._debounce_seconds = 2

    def on_created(self, event):
        """Handle file created event."""
        if not event.is_directory and self._is_markdown_file(event.src_path):
            if not self._is_excluded(event.src_path):
                self._debounce_event(event.src_path)

    def on_modified(self, event):
        """Handle file modified event."""
        if not event.is_directory and self._is_markdown_file(event.src_path):
            if not self._is_excluded(event.src_path):
                self._debounce_event(event.src_path)

    def _is_markdown_file(self, path: str) -> bool:
        """Check if a file is a markdown file."""
        return path.lower().endswith(('.md', '.markdown'))

    def _is_excluded(self, path: str) -> bool:
        """Check if a path matches any excluded patterns."""
        for pattern in self.excluded_patterns:
            # Simple glob pattern matching
            if pattern.endswith('/**'):
                # Directory and all subdirectories
                dir_pattern = pattern[:-3]
                if path.startswith(dir_pattern):
                    return True
            elif pattern.startswith('*') and pattern.endswith('*'):
                # Contains pattern
                middle = pattern[1:-1]
                if middle in path:
                    return True
            elif pattern.startswith('*'):
                # Ends with pattern
                suffix = pattern[1:]
                if path.endswith(suffix):
                    return True
            elif pattern.endswith('*'):
                # Starts with pattern
                prefix = pattern[:-1]
                if path.startswith(prefix):
                    return True
            elif pattern == path:
                # Exact match
                return True
        return False

    def _debounce_event(self, path: str):
        """
        Debounce file events to prevent multiple callbacks for the same change.
        """
        current_time = time.time()
        last_time = self._last_events.get(path, 0)
        
        self._last_events[path] = current_time
        
        # If enough time has passed since the last event, process it
        if current_time - last_time > self._debounce_seconds:
            # Schedule the callback to run after debounce period
            # In a real implementation, we might use a proper job queue
            time.sleep(self._debounce_seconds)
            
            # Check if this is still the most recent event
            if self._last_events.get(path) == current_time:
                self.callback(path)


class FileWatcher:
    """Watches for changes in markdown files and triggers sync actions."""

    def __init__(self, config: Config, callback: Callable[[str], None]):
        """
        Initialize file watcher.

        Args:
            config: Application configuration.
            callback: Function to call when a markdown file is changed.
        """
        self.config = config
        self.callback = callback
        self.markdown_root = config.get("directories.markdown_root", "./docs")
        self.observer = None

    def start(self, daemon: bool = False) -> None:
        """
        Start watching for file changes.

        Args:
            daemon: Run as a daemon process.
        """
        if not os.path.exists(self.markdown_root):
            os.makedirs(self.markdown_root, exist_ok=True)
            
        event_handler = MarkdownFileEventHandler(self.callback, self.config)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.markdown_root, recursive=True)
        
        self.observer.start()
        
        if not daemon:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
                
    def stop(self) -> None:
        """Stop watching for file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None