import time
import threading
class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_checked = time.time()
        self.lock = threading.Lock()
    def acquire(self):
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_checked
                self.last_checked = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

                if self.tokens >= 1:
                    # 有足夠的令牌，消耗一個令牌
                    self.tokens -= 1
                    return
            time.sleep(0.1)