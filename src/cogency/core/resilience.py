"""Production resilience: Rate limiting, circuit breakers, retries."""

import asyncio
import os
import time
import logging
from typing import Dict, Any, Callable, Optional, Awaitable
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import random


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    timeout: float = 30.0


@dataclass
class RateLimiterConfig:
    requests_per_minute: int = int(os.getenv("COGENCY_RATE_LIMIT_RPM", "300"))
    burst_size: int = int(os.getenv("COGENCY_RATE_LIMIT_BURST", "50"))
    backoff_multiplier: float = float(os.getenv("COGENCY_RATE_LIMIT_BACKOFF", "2.0"))
    max_backoff: float = float(os.getenv("COGENCY_RATE_LIMIT_MAX_BACKOFF", "60.0"))
    jitter: bool = os.getenv("COGENCY_RATE_LIMIT_JITTER", "true").lower() == "true"


@dataclass
class CircuitBreakerState:
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    next_attempt_time: float = 0


class RateLimiter:
    """Token bucket rate limiter with intelligent backoff."""
    
    def __init__(self, config: RateLimiterConfig):
        self.config = config
        self.tokens = config.burst_size
        self.last_refill = time.time()
        self.backoff_until = 0
        self.consecutive_limits = 0
    
    async def acquire(self) -> bool:
        """Acquire permission to make request."""
        now = time.time()
        
        # Check if we're in backoff period
        if now < self.backoff_until:
            return False
        
        # Refill tokens
        time_passed = now - self.last_refill
        new_tokens = time_passed * (self.config.requests_per_minute / 60.0)
        self.tokens = min(self.config.burst_size, self.tokens + new_tokens)
        self.last_refill = now
        
        # Check if we have tokens
        if self.tokens >= 1:
            self.tokens -= 1
            self.consecutive_limits = 0
            return True
        
        # Rate limited - implement backoff
        self.consecutive_limits += 1
        backoff_time = min(
            self.config.max_backoff,
            (self.config.backoff_multiplier ** self.consecutive_limits)
        )
        
        if self.config.jitter:
            backoff_time *= (0.5 + 0.5 * random.random())
        
        self.backoff_until = now + backoff_time
        return False
    
    def get_wait_time(self) -> float:
        """Get time until next request allowed."""
        now = time.time()
        if now >= self.backoff_until:
            return max(0, (1 - self.tokens) * (60.0 / self.config.requests_per_minute))
        return self.backoff_until - now


class CircuitBreaker:
    """Circuit breaker for external dependencies."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState()
        self.logger = logging.getLogger(f"circuit_breaker.{name}")
    
    async def call(self, func: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        now = time.time()
        
        # Check circuit state
        if self.state.state == CircuitState.OPEN:
            if now < self.state.next_attempt_time:
                raise CircuitOpenError(f"Circuit {self.name} is open")
            else:
                # Try half-open
                self.state.state = CircuitState.HALF_OPEN
                self.state.success_count = 0
                self.logger.info(f"Circuit {self.name} attempting recovery")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            # Success
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure(e)
            raise
    
    async def _on_success(self):
        """Handle successful call."""
        if self.state.state == CircuitState.HALF_OPEN:
            self.state.success_count += 1
            if self.state.success_count >= self.config.success_threshold:
                self.state.state = CircuitState.CLOSED
                self.state.failure_count = 0
                self.logger.info(f"Circuit {self.name} recovered")
        elif self.state.state == CircuitState.CLOSED:
            self.state.failure_count = 0
    
    async def _on_failure(self, error: Exception):
        """Handle failed call."""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()
        
        if self.state.state == CircuitState.HALF_OPEN:
            # Failed during recovery, go back to open
            self.state.state = CircuitState.OPEN
            self.state.next_attempt_time = time.time() + self.config.recovery_timeout
            self.logger.warning(f"Circuit {self.name} failed recovery: {error}")
        elif (self.state.state == CircuitState.CLOSED and 
              self.state.failure_count >= self.config.failure_threshold):
            # Too many failures, open circuit
            self.state.state = CircuitState.OPEN
            self.state.next_attempt_time = time.time() + self.config.recovery_timeout
            self.logger.error(f"Circuit {self.name} opened due to failures: {error}")


class ResilienceManager:
    """Manages rate limiters and circuit breakers."""
    
    def __init__(self):
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logging.getLogger("resilience")
    
    def get_rate_limiter(self, name: str, config: Optional[RateLimiterConfig] = None) -> RateLimiter:
        """Get or create rate limiter."""
        if name not in self.rate_limiters:
            if config is None:
                config = RateLimiterConfig()
            self.rate_limiters[name] = RateLimiter(config)
        return self.rate_limiters[name]
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker."""
        if name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]


# Global resilience manager
_resilience_manager = ResilienceManager()


class CircuitOpenError(Exception):
    """Circuit breaker is open."""
    pass


class RateLimitedError(Exception):
    """Request was rate limited."""
    pass


def with_resilience(
    rate_limiter: Optional[str] = None,
    circuit_breaker: Optional[str] = None,
    rate_config: Optional[RateLimiterConfig] = None,
    circuit_config: Optional[CircuitBreakerConfig] = None
):
    """Decorator to add resilience to async functions."""
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting
            if rate_limiter:
                limiter = _resilience_manager.get_rate_limiter(rate_limiter, rate_config)
                if not await limiter.acquire():
                    wait_time = limiter.get_wait_time()
                    raise RateLimitedError(f"Rate limited, wait {wait_time:.1f}s")
            
            # Circuit breaker
            if circuit_breaker:
                breaker = _resilience_manager.get_circuit_breaker(circuit_breaker, circuit_config)
                return await breaker.call(func, *args, **kwargs)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """Decorator for exponential backoff retry."""
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        break
                    
                    # Calculate delay
                    delay = min(max_delay, base_delay * (backoff_factor ** attempt))
                    if jitter:
                        delay *= (0.5 + 0.5 * random.random())
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator