from cogency.core.circuit import CircuitBreaker


def test_init():
    cb = CircuitBreaker(max_failures=3)
    assert not cb.is_open()
    assert cb.consecutive_failures == 0


def test_opens_at_threshold():
    cb = CircuitBreaker(max_failures=3)

    assert not cb.record_failure()
    assert not cb.record_failure()
    assert cb.record_failure()
    assert cb.is_open()


def test_resets_on_success():
    cb = CircuitBreaker(max_failures=3)

    cb.record_failure()
    cb.record_failure()
    cb.record_success()

    assert cb.consecutive_failures == 0
    assert not cb.is_open()
