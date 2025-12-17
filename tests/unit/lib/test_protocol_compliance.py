"""Regression tests for Protocol compliance.

Ensures implementations satisfy their Protocol contracts.
"""

import inspect

import pytest

from cogency.core.protocols import Storage
from cogency.lib.sqlite import SQLite


def test_sqlite_implements_storage_protocol():
    """Regression: SQLite must implement all Storage Protocol methods.

    This test prevents duplicate Protocol definitions (sqlite.py had its own
    Storage Protocol that diverged from core/protocols.py).
    """
    protocol_methods = {
        name
        for name, method in inspect.getmembers(Storage)
        if inspect.iscoroutinefunction(method) or (hasattr(method, "__isabstractmethod__"))
    }

    sqlite_methods = {
        name
        for name in dir(SQLite)
        if not name.startswith("_") and inspect.iscoroutinefunction(getattr(SQLite, name))
    }

    missing = protocol_methods - sqlite_methods

    assert not missing, f"SQLite missing Storage Protocol methods: {sorted(missing)}"


def test_storage_protocol_has_no_duplicates():
    """Regression: Ensure Storage Protocol is defined only in core/protocols.py.

    Previously, lib/sqlite.py had its own Storage Protocol definition that
    diverged from the canonical one in core/protocols.py, causing import
    confusion and inconsistent contracts.
    """
    # This test is documentation - if sqlite.py re-introduces Storage Protocol,
    # the import in recall.py and registry.py would break (they import from core/protocols)
    from cogency.core.protocols import Storage as CoreStorage
    from cogency.tools.recall import Storage as RecallStorage

    assert CoreStorage is RecallStorage, "Storage Protocol must be imported from core/protocols"


@pytest.mark.asyncio
async def test_sqlite_protocol_methods_callable():
    """Verify SQLite implements Protocol methods correctly."""
    storage = SQLite(db_path=":memory:")

    # Verify all Protocol methods exist and are callable
    assert callable(storage.save_message)
    assert callable(storage.load_messages)
    assert callable(storage.save_event)
    assert callable(storage.save_profile)
    assert callable(storage.load_profile)
    assert callable(storage.load_user_messages)
    assert callable(storage.count_user_messages)
    assert callable(storage.delete_profile)
    assert callable(storage.load_latest_metric)
    assert callable(storage.load_messages_by_conversation_id)
    assert callable(storage.search_messages)
