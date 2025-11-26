import threading
from config import MAX_CACHE_ENTRIES


class Cache:
    def __init__(self):
        self.storage = {}
        self.lock = threading.Lock()

    def get(self, url):
        with self.lock:
            return self.storage.get(url)

    def save(self, url, data, headers):
        with self.lock:
            if len(self.storage) >= MAX_CACHE_ENTRIES:
                self.storage.pop(next(iter(self.storage)))

            self.storage[url] = {
                'data': data,
                'headers': headers
            }

    def get_size(self):
        with self.lock: return len(self.storage)