"""Result tests."""

import pytest

from cogency.core.result import Err, Ok


def test_result_behavior():
    """Result handles success/failure, unwrap, flattening, truthiness."""

    # Success behavior
    ok = Ok("data")
    assert ok.success is True
    assert ok.failure is False
    assert ok.error is None
    assert ok.unwrap() == "data"
    assert bool(ok) is True
    assert repr(ok) == "Ok('data')"

    # Failure behavior
    err = Err("error")
    assert err.success is False
    assert err.failure is True
    assert err.error == "error"
    assert bool(err) is False
    assert repr(err) == "Err('error')"

    # Unwrap failure
    with pytest.raises(ValueError, match="Cannot unwrap failed result: error"):
        err.unwrap()

    # Autoflattening
    nested_ok = Ok(Ok("data"))
    assert nested_ok.success
    assert nested_ok.unwrap() == "data"

    nested_err = Err(Err("error"))
    assert nested_err.failure
    assert nested_err.error == "error"

    # Mixed nesting - Ok(Err) returns the Err
    mixed = Ok(Err("error"))
    assert mixed is Err("error") or (mixed.failure and mixed.error == "error")

    # Edge cases
    assert Ok(None).unwrap() is None
    assert Ok("").unwrap() == ""
    assert Ok(0).unwrap() == 0
    assert bool(Ok(False)) is True  # Ok is truthy even with falsy data

    # Err(None) should raise
    with pytest.raises(ValueError, match="Err\\(None\\) is invalid"):
        Err(None)
