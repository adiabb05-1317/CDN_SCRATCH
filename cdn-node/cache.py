from collections import OrderedDict
from typing import Optional

class LRUCache:
    def __init__(self, max_size: int = 10 * 1024 * 1024):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.current_size = 0
    
    def get(self, key: str) -> Optional[bytes]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: bytes):
        if key in self.cache:
            self.current_size -= len(self.cache[key])
            self.cache.move_to_end(key)
        
        self.cache[key] = value
        self.current_size += len(value)
        
        while self.current_size > self.max_size and self.cache:
            oldest_key, oldest_value = self.cache.popitem(last=False)
            self.current_size -= len(oldest_value)
    
    def delete(self, key: str):
        if key in self.cache:
            self.current_size -= len(self.cache[key])
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()
        self.current_size = 0
