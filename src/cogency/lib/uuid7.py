"""UUID v7 generation for time-ordered distributed IDs.

Implements RFC 9562 UUID v7 spec with monotonic counter:
- 48-bit Unix timestamp (milliseconds)
- 4-bit version (0111 = 7)
- 12-bit monotonic counter (increments within same millisecond)
- 2-bit variant (10)
- 62-bit random

Provides chronological ordering + global uniqueness without coordination.

DEPRECATION: Python 3.13+ includes native uuid.uuid7(). This fallback implementation
supports 3.11-3.12 but will be removed when cogency requires Python 3.13+.
"""

import secrets
import threading
import time
import uuid
import warnings

# Monotonic state for same-millisecond IDs (RFC 9562 Method 2)
_state_lock = threading.Lock()
_last_timestamp_ms = 0
_counter = 0

# Check for native uuid7 support once at module load
_USE_NATIVE = hasattr(uuid, "uuid7")

# Warn once if using fallback implementation
if not _USE_NATIVE:
    warnings.warn(
        "Using fallback UUID7 implementation. "
        "Python 3.13+ includes native uuid.uuid7() with better performance. "
        "This fallback will be removed when cogency requires Python 3.13+.",
        DeprecationWarning,
        stacklevel=2,
    )


def uuid7() -> str:
    """Generate UUID v7 (time-ordered) for distributed-safe IDs."""
    if _USE_NATIVE:
        return str(uuid.uuid7())  # type: ignore[attr-defined]

    global _last_timestamp_ms, _counter

    with _state_lock:
        timestamp_ms = int(time.time() * 1000)

        # RFC 9562 Method 2: Monotonic counter for same-millisecond IDs
        if timestamp_ms == _last_timestamp_ms:
            _counter = (_counter + 1) & 0xFFF  # 12-bit counter wraps
        else:
            _counter = secrets.randbits(12)
            _last_timestamp_ms = timestamp_ms

        # RFC 9562: 48-bit timestamp + 4-bit version + 12-bit counter
        time_high = (timestamp_ms >> 16) & 0xFFFFFFFF
        time_low = timestamp_ms & 0xFFFF

        # Version field: 0111 (7) in bits 12-15
        time_low_and_version = (time_low << 16) | (7 << 12) | _counter

        # Variant field: 10 in bits 0-1, followed by 62 bits random
        rand_b_high = secrets.randbits(14)
        rand_b_low = secrets.randbits(48)
        variant_and_rand = (0b10 << 62) | (rand_b_high << 48) | rand_b_low

        # Assemble 128-bit UUID
        uuid_int = (time_high << 96) | (time_low_and_version << 64) | variant_and_rand

        return str(uuid.UUID(int=uuid_int))
