"""Result monadic foundation destruction tests.

DESTRUCTION MATRIX:
1. Autoflattening - prevent nested Result hell
2. Unwrap discipline - fail fast on error unwrap
3. Truthiness - boolean logic correctness
4. Edge cases - None/empty/weird data
5. Type safety - generic constraints
6. Repr consistency - debugging clarity
"""

import pytest

from cogency.core.result import Err, Ok, Result


def test_autoflattening_ok_nesting():
    """DESTROY: Ok(Ok(data)) nesting prevention."""
    # Single level
    result1 = Ok("data")
    assert result1.success
    assert result1.unwrap() == "data"

    # Nested Ok - should flatten
    result2 = Ok(Ok("data"))
    assert result2.success
    assert result2.unwrap() == "data"
    # Autoflattening returns same data, but different objects (acceptable)

    # Triple nesting - should flatten
    result3 = Ok(Ok(Ok("data")))
    assert result3.success
    assert result3.unwrap() == "data"


# Autoflattening returns same data, but different objects (acceptable)


def test_autoflattening_err_nesting():
    """DESTROY: Err(Err(error)) nesting prevention."""
    # Single level
    result1 = Err("error")
    assert result1.failure
    assert result1.error == "error"

    # Nested Err - should flatten
    result2 = Err(Err("error"))
    assert result2.failure
    assert result2.error == "error"
    # Autoflattening returns same data, but different objects (acceptable)

    # Triple nesting - should flatten
    result3 = Err(Err(Err("error")))
    assert result3.failure
    assert result3.error == "error"


# Autoflattening returns same data, but different objects (acceptable)


def test_autoflattening_mixed_nesting():
    """DESTROY: Ok(Err()) and Err(Ok()) edge cases."""
    # Ok containing Err - should return the Err
    err_result = Err("error")
    mixed_result = Ok(err_result)
    assert mixed_result is err_result
    assert mixed_result.failure
    assert mixed_result.error == "error"

    # Err containing successful Ok - should preserve as error data
    ok_result = Ok("data")
    err_with_ok = Err(ok_result)
    assert err_with_ok.failure
    assert err_with_ok.error is ok_result


def test_unwrap_destruction():
    """DESTROY: Every way unwrap can fail."""
    # Success unwrap
    ok_result = Ok("data")
    assert ok_result.unwrap() == "data"

    # Failure unwrap - should crash
    err_result = Err("error")
    with pytest.raises(ValueError) as exc_info:
        err_result.unwrap()
    assert "Cannot unwrap failed result: error" in str(exc_info.value)

    # None data unwrap - should return None
    none_result = Ok(None)
    assert none_result.unwrap() is None

    # Empty string unwrap - should return empty string
    empty_result = Ok("")
    assert empty_result.unwrap() == ""


def test_boolean_truthiness_destruction():
    """DESTROY: Boolean logic edge cases."""
    # Success cases - truthy
    assert Ok("data")
    assert Ok(0)  # Even falsy data is truthy Result
    assert Ok(False)  # Even False data is truthy Result
    assert Ok(None)  # Even None data is truthy Result
    assert Ok("")  # Even empty data is truthy Result

    # Failure cases - falsy
    assert not Err("error")
    assert not Err("")  # Even empty error is falsy Result
    # Err(None) should raise - invalid construction
    assert not Err(0)  # Even zero error is falsy Result


def test_property_access_destruction():
    """DESTROY: Property access edge cases."""
    # Success properties
    ok_result = Ok("data")
    assert ok_result.success is True
    assert ok_result.failure is False
    assert ok_result.error is None

    # Failure properties
    err_result = Err("error")
    assert err_result.success is False
    assert err_result.failure is True
    assert err_result.error == "error"

    # Edge case: None error
    none_err = Result(error=None)  # Direct construction
    assert none_err.success is True
    assert none_err.failure is False


def test_repr_consistency_destruction():
    """DESTROY: String representation edge cases."""
    # Success repr
    ok_result = Ok("data")
    assert repr(ok_result) == "Ok('data')"

    # Failure repr
    err_result = Err("error")
    assert repr(err_result) == "Err('error')"

    # Complex data repr
    complex_ok = Ok({"key": "value", "list": [1, 2, 3]})
    assert repr(complex_ok) == "Ok({'key': 'value', 'list': [1, 2, 3]})"

    # None cases
    none_ok = Ok(None)
    assert repr(none_ok) == "Ok(None)"

    # Err(None) should raise - test in separate function


def test_edge_case_destruction():
    """DESTROY: Weird data types and edge cases."""

    # Function as data
    def test_fn():
        return "test"

    fn_result = Ok(test_fn)
    assert fn_result.success
    assert fn_result.unwrap() is test_fn

    # Exception as data
    ex_result = Ok(ValueError("test"))
    assert ex_result.success
    assert isinstance(ex_result.unwrap(), ValueError)

    # Result as error data
    inner_result = Ok("inner")
    outer_err = Err(inner_result)
    assert outer_err.failure
    assert outer_err.error is inner_result

    # Large data
    big_data = "x" * 10000
    big_result = Ok(big_data)
    assert big_result.success
    assert len(big_result.unwrap()) == 10000


def test_err_none_destruction():
    """DESTROY: Err(None) should crash - invalid construction."""
    with pytest.raises(ValueError) as exc_info:
        Err(None)
    assert "Err(None) is invalid" in str(exc_info.value)


def test_type_safety_destruction():
    """DESTROY: Generic type constraints."""
    # String Result
    str_result: Result[str, str] = Ok("data")
    assert isinstance(str_result.unwrap(), str)

    # Int Result
    int_result: Result[int, str] = Ok(42)
    assert isinstance(int_result.unwrap(), int)

    # List Result
    list_result: Result[list, str] = Ok([1, 2, 3])
    assert isinstance(list_result.unwrap(), list)

    # Dict Result
    dict_result: Result[dict, str] = Ok({"key": "value"})
    assert isinstance(dict_result.unwrap(), dict)


if __name__ == "__main__":
    print("🔥 RESULT MONADIC FOUNDATION DESTRUCTION 🔥")
    print("=" * 50)

    test_autoflattening_ok_nesting()
    test_autoflattening_err_nesting()
    test_autoflattening_mixed_nesting()
    test_unwrap_destruction()
    test_boolean_truthiness_destruction()
    test_property_access_destruction()
    test_repr_consistency_destruction()
    test_edge_case_destruction()
    test_err_none_destruction()
    test_type_safety_destruction()

    print("🎯 MONADIC DESTRUCTION COMPLETE - FOUNDATION VALIDATED")
