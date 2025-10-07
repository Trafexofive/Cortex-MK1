"""
==============================================================================
HOT-RELOAD WATCHER v1.0
==============================================================================
Filesystem watcher that monitors manifest directories and triggers automatic
reload when manifests are added, modified, or deleted.

Enables FAAFO-friendly rapid iteration without service restarts.
==============================================================================
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable, Awaitable, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from loguru import logger


class ManifestFileHandler(FileSystemEventHandler):
    """
    Handles filesystem events for manifest files.
    Filters for .yml, .yaml, and .md files only.
    """
    
    def __init__(self, callback: Callable[[str, str], Awaitable[None]], loop: asyncio.AbstractEventLoop):
        """
        Args:
            callback: Async callback function(event_type, file_path)
            loop: Event loop to schedule async callbacks
        """
        self.callback = callback
        self.loop = loop
        self.valid_extensions = {'.yml', '.yaml', '.md', '.markdown'}
        self._processing: Set[str] = set()
        
    def _should_process(self, path: str) -> bool:
        """Check if file should be processed"""
        file_path = Path(path)
        
        # Ignore hidden files and directories
        if any(part.startswith('.') for part in file_path.parts):
            return False
            
        # Only process valid manifest extensions
        if file_path.suffix.lower() not in self.valid_extensions:
            return False
            
        return True
    
    def _schedule_callback(self, event_type: str, file_path: str):
        """Schedule async callback in the event loop"""
        # Prevent duplicate processing of the same event
        key = f"{event_type}:{file_path}"
        if key in self._processing:
            return
            
        self._processing.add(key)
        
        async def wrapped_callback():
            try:
                await self.callback(event_type, file_path)
            finally:
                self._processing.discard(key)
        
        asyncio.run_coroutine_threadsafe(wrapped_callback(), self.loop)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if not event.is_directory and self._should_process(event.src_path):
            logger.debug(f"📄 Manifest created: {event.src_path}")
            self._schedule_callback("created", event.src_path)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if not event.is_directory and self._should_process(event.src_path):
            logger.debug(f"✏️  Manifest modified: {event.src_path}")
            self._schedule_callback("modified", event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events"""
        if not event.is_directory and self._should_process(event.src_path):
            logger.debug(f"🗑️  Manifest deleted: {event.src_path}")
            self._schedule_callback("deleted", event.src_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events"""
        if not event.is_directory:
            # Treat move as delete + create
            if self._should_process(event.src_path):
                logger.debug(f"📦 Manifest moved from: {event.src_path}")
                self._schedule_callback("deleted", event.src_path)
            if hasattr(event, 'dest_path') and self._should_process(event.dest_path):
                logger.debug(f"📦 Manifest moved to: {event.dest_path}")
                self._schedule_callback("created", event.dest_path)


class HotReloadWatcher:
    """
    Watches manifest directories for changes and triggers automatic reloads.
    """
    
    def __init__(
        self, 
        manifest_root: Path,
        reload_callback: Callable[[str, str], Awaitable[None]],
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """
        Args:
            manifest_root: Root directory containing manifests
            reload_callback: Async callback(event_type, file_path) to handle reloads
            loop: Event loop (uses current loop if not provided)
        """
        self.manifest_root = Path(manifest_root)
        self.reload_callback = reload_callback
        self.loop = loop or asyncio.get_event_loop()
        
        self.observer: Optional[Observer] = None
        self._running = False
        
    def start(self):
        """Start watching the manifest directory"""
        if self._running:
            logger.warning("Hot-reload watcher already running")
            return
            
        if not self.manifest_root.exists():
            logger.error(f"Manifest root does not exist: {self.manifest_root}")
            raise FileNotFoundError(f"Manifest directory not found: {self.manifest_root}")
        
        # Create event handler
        event_handler = ManifestFileHandler(self.reload_callback, self.loop)
        
        # Create and configure observer
        self.observer = Observer()
        self.observer.schedule(
            event_handler, 
            str(self.manifest_root), 
            recursive=True  # Watch subdirectories
        )
        
        # Start the observer thread
        self.observer.start()
        self._running = True
        
        logger.info(f"🔥 Hot-reload watcher started for: {self.manifest_root}")
        logger.info("🔄 Monitoring for manifest changes (add, modify, delete)...")
    
    def stop(self):
        """Stop watching the manifest directory"""
        if not self._running or not self.observer:
            return
            
        self.observer.stop()
        self.observer.join()
        self._running = False
        
        logger.info("🛑 Hot-reload watcher stopped")
    
    def is_running(self) -> bool:
        """Check if the watcher is currently running"""
        return self._running
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
