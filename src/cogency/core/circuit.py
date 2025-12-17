class CircuitBreaker:
    def __init__(self, max_failures: int = 3):
        self.max_failures = max_failures
        self.consecutive_failures = 0

    def record_success(self):
        self.consecutive_failures = 0

    def record_failure(self) -> bool:
        self.consecutive_failures += 1
        return self.consecutive_failures >= self.max_failures

    def is_open(self) -> bool:
        return self.consecutive_failures >= self.max_failures
