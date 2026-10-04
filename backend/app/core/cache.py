import time
from typing import Any, Dict, Tuple, Optional

class MemoryCacheProvider:
    def __init__(self):
        # key -> (value, expires_at)
        self.store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.store:
            value, expires_at = self.store[key]
            if time.time() > expires_at:
                del self.store[key]
                return None
            return value
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self.store[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str):
        if key in self.store:
            del self.store[key]
            
    def clear(self):
        self.store.clear()

cache = MemoryCacheProvider()
