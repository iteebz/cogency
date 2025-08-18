"""Storage layer tests - type preservation and file operations."""

from pathlib import Path
from tempfile import NamedTemporaryFile
import json

from cogency.lib.storage import load_json_file, save_json_file


def test_list_default_preserved():
    """Default list type preserved when file missing."""
    nonexistent = Path("nonexistent_file_12345.json")
    result = load_json_file(nonexistent, [])
    assert isinstance(result, list)
    assert result == []


def test_dict_default_preserved():
    """Default dict type preserved when file missing."""
    nonexistent = Path("nonexistent_file_12345.json") 
    result = load_json_file(nonexistent, {})
    assert isinstance(result, dict)
    assert result == {}


def test_none_defaults_to_dict():
    """None default returns empty dict."""
    nonexistent = Path("nonexistent_file_12345.json")
    result = load_json_file(nonexistent, None)
    assert isinstance(result, dict)
    assert result == {}


def test_roundtrip_list():
    """List data roundtrip through save/load."""
    test_data = ["item1", "item2", "item3"]
    
    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        save_json_file(temp_path, test_data)
        loaded = load_json_file(temp_path, [])
        
        assert isinstance(loaded, list)
        assert loaded == test_data
    finally:
        temp_path.unlink(missing_ok=True)


def test_roundtrip_dict():
    """Dict data roundtrip through save/load."""
    test_data = {"key": "value", "count": 42}
    
    with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        save_json_file(temp_path, test_data)
        loaded = load_json_file(temp_path, {})
        
        assert isinstance(loaded, dict)
        assert loaded == test_data
    finally:
        temp_path.unlink(missing_ok=True)