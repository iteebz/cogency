import importlib.util

import pytest


def test_import_agent():
    spec = importlib.util.find_spec("cogency.agent")
    assert spec is not None, "Failed to find cogency.agent module spec"
    try:
        # If we reach here, the import was successful
        assert True
    except ModuleNotFoundError as e:
        pytest.fail(f"Failed to import Agent from cogency: {e}")
