"""Essential tests for canonical Result type."""

from cogency.lib import Err, Ok


def test_ok():
    """Ok constructor and unwrap."""
    result = Ok("data")
    assert result.success
    assert result.unwrap() == "data"


def test_err():
    """Err constructor and error access."""
    result = Err("error")
    assert result.failure
    assert result.error == "error"


def test_flatten():
    """Autoflattening prevents nesting."""
    nested = Ok(Ok("data"))
    assert nested.unwrap() == "data"

    # Ok containing Err becomes Err
    mixed = Ok(Err("error"))
    assert mixed.failure
    assert mixed.error == "error"


def test_unwrap_fails():
    """Unwrap failed result raises exception."""
    result = Err("error")
    try:
        result.unwrap()
        raise AssertionError()
    except ValueError:
        pass
