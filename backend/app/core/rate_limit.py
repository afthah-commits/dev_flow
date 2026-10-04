import time
from typing import Dict, Tuple
from fastapi import HTTPException, Request

class MemoryRateLimiter:
    def __init__(self):
        # key -> (count, reset_time)
        self.store: Dict[str, Tuple[int, float]] = {}

    def check(self, key: str, limit: int, window: int):
        now = time.time()
        
        # Cleanup old entries occasionally to prevent memory leak
        if len(self.store) > 10000:
            self.store = {k: v for k, v in self.store.items() if v[1] > now}
            
        if key in self.store:
            count, reset_time = self.store[key]
            if now > reset_time:
                # Window expired, reset
                self.store[key] = (1, now + window)
            else:
                if count >= limit:
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Try again later.",
                        headers={"Retry-After": str(int(reset_time - now))}
                    )
                self.store[key] = (count + 1, reset_time)
        else:
            self.store[key] = (1, now + window)

limiter = MemoryRateLimiter()

def rate_limit(limit: int, window: int):
    """
    Dependency to rate limit an endpoint.
    Example: Depends(rate_limit(5, 60)) # 5 requests per 60 seconds
    """
    def dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rl:{client_ip}:{path}"
        limiter.check(key, limit, window)
    return dependency
