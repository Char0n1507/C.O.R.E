import asyncio
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogEventHandler(FileSystemEventHandler):
    """
    Handles file system events for log files.
    When a log file is modified, it reads the new lines and sends them for processing.
    """
    def __init__(self, processing_queue, loop, log_paths):
        self.processing_queue = processing_queue
        self.loop = loop
        self.log_paths = log_paths
        self.file_cursors = {} # Keep track of file positions

    def on_modified(self, event):
        if event.is_directory:
            return
        
        filepath = os.path.abspath(event.src_path)
        # Verify it's in our designated log paths 
        if not any(filepath == os.path.abspath(lp) for lp in self.log_paths):
            return

        self.process_new_lines(filepath)

    def process_new_lines(self, filepath):
        """Reads only new lines appended to the file."""
        try:
            current_size = os.path.getsize(filepath)
            last_position = self.file_cursors.get(filepath, 0)
            
            if current_size < last_position:
                # File was truncated (log rotation), reset cursor
                last_position = 0
            
            if current_size == last_position:
                return # No new data

            with open(filepath, 'r') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                self.file_cursors[filepath] = f.tell()

            for line in new_lines:
                line = line.strip()
                if line:
                    # Send to async queue safely from this thread
                    asyncio.run_coroutine_threadsafe(
                        self.processing_queue.put({"source": filepath, "content": line, "timestamp": time.time()}),
                        self.loop
                    )
        except Exception as e:
            print(f"[!] Error reading log {filepath}: {e}")
            pass

class LogMonitor:
    """
    Orchestrates monitoring of multiple log files/directories.
    """
    def __init__(self, log_paths, processing_queue, loop):
        self.log_paths = log_paths
        self.processing_queue = processing_queue
        self.loop = loop
        self.observer = Observer()
        self.handler = LogEventHandler(processing_queue, loop, log_paths)

    def start(self):
        print(f"[*] Starting LogMonitor on {len(self.log_paths)} paths...")
        for path in self.log_paths:
            path = os.path.abspath(path)
            
            # Initialize cursor at the end of the file to skip existing logs
            if os.path.isfile(path):
                self.handler.file_cursors[path] = os.path.getsize(path)
            
            if os.path.isdir(path):
                self.observer.schedule(self.handler, path, recursive=False)
            elif os.path.isfile(path) or not os.path.exists(path):
                # Watchdog watches directories, so we watch the parent dir
                if not os.path.exists(path):
                    print(f"[!] Path not found: {path} (Creating it...)")
                    with open(path, 'a'): pass
                    self.handler.file_cursors[path] = 0
                
                parent_dir = os.path.dirname(path)
                self.observer.schedule(self.handler, parent_dir, recursive=False)

        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
