from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
import subprocess
import time
from datetime import datetime

class MyHandler(FileSystemEventHandler):
    def __init__(self, build_directory, content_directory, ignore_patterns=None):
        super().__init__()
        self.build_directory = build_directory
        self.content_directory = content_directory
        self.ignore_patterns = ignore_patterns or []

    def should_ignore_event(self, path):
        for pattern in self.ignore_patterns:
            if pattern in path:
                return True
        return False
    
    def on_any_event(self, event):
        if self.should_ignore_event(event.src_path) or event.is_directory:
            return
        file_name = event.src_path.split('/')[-1]
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} -- {file_name} has been {event.event_type}')
        try:
            print('Woof woof! Building the site...')
            subprocess.run('cf')
        except subprocess.CalledProcessError as e:
            print(f'Error: {e}')

def start_watching(build_directory, content_directory):
    ignore_patterns = ['__pycache__', '.git', '.DS_Store', 'no-watchdogs-allowed', '.obsidian', '.css.map', '.scss']
    event_handler = MyHandler(build_directory, content_directory, ignore_patterns)
    observer = Observer()
    paths = [build_directory, content_directory]
    for path in paths:
        observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print('Watchdog is waiting for changes! Woof!')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()