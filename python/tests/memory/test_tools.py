"""Tests for memory tools."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from cogency.memory.tools import MemorizeTool, RecallTool
from cogency.memory.base import MemoryArtifact


@pytest.fixture
def mock_memory():
    """Create mock memory backend."""
    return AsyncMock()


@pytest.fixture
def memorize_tool(mock_memory):
    """Create MemorizeTool with mock memory."""
    return MemorizeTool(mock_memory)


@pytest.fixture
def recall_tool(mock_memory):
    """Create RecallTool with mock memory."""
    return RecallTool(mock_memory)


def test_memorize_tool_initialization(memorize_tool):
    """Test MemorizeTool initialization."""
    assert memorize_tool.name == "memorize"
    assert "memory" in memorize_tool.description.lower()


def test_recall_tool_initialization(recall_tool):
    """Test RecallTool initialization."""
    assert recall_tool.name == "recall"
    assert "memory" in recall_tool.description.lower()


@pytest.mark.asyncio
async def test_memorize_tool_run_success(memorize_tool, mock_memory):
    """Test successful memorize tool execution."""
    # Setup mock
    artifact = MemoryArtifact(content="Test content", tags=["test"])
    mock_memory.memorize.return_value = artifact
    
    # Run tool
    result = await memorize_tool.run(
        content="Test content",
        tags=["test"],
        metadata={"priority": "high"}
    )
    
    # Verify mock was called correctly
    mock_memory.memorize.assert_called_once_with(
        "Test content",
        tags=["test"],
        metadata={"priority": "high"}
    )
    
    # Verify result
    assert result["success"] is True
    assert result["artifact_id"] == str(artifact.id)
    assert result["content_preview"] == "Test content"
    assert result["tags"] == ["test"]


@pytest.mark.asyncio
async def test_memorize_tool_run_missing_content(memorize_tool):
    """Test memorize tool with missing content parameter."""
    result = await memorize_tool.run()
    
    assert "error" in result
    assert "content parameter is required" in result["error"]


@pytest.mark.asyncio
async def test_memorize_tool_run_with_defaults(memorize_tool, mock_memory):
    """Test memorize tool with default parameters."""
    artifact = MemoryArtifact(content="Test content")
    mock_memory.memorize.return_value = artifact
    
    result = await memorize_tool.run(content="Test content")
    
    mock_memory.memorize.assert_called_once_with("Test content", tags=[], metadata={})
    assert result["success"] is True


@pytest.mark.asyncio
async def test_memorize_tool_run_exception(memorize_tool, mock_memory):
    """Test memorize tool handling exceptions."""
    mock_memory.memorize.side_effect = Exception("Memory error")
    
    result = await memorize_tool.run(content="Test content")
    
    assert "error" in result
    assert "Failed to memorize content" in result["error"]


@pytest.mark.asyncio
async def test_memorize_tool_long_content_preview(memorize_tool, mock_memory):
    """Test content preview truncation for long content."""
    long_content = "A" * 150
    artifact = MemoryArtifact(content=long_content)
    mock_memory.memorize.return_value = artifact
    
    result = await memorize_tool.run(content=long_content)
    
    assert result["success"] is True
    assert len(result["content_preview"]) <= 103  # 100 + "..."
    assert result["content_preview"].endswith("...")


@pytest.mark.asyncio
async def test_recall_tool_run_success(recall_tool, mock_memory):
    """Test successful recall tool execution."""
    # Setup mock
    artifact1 = MemoryArtifact(content="Content 1", tags=["test"])
    artifact2 = MemoryArtifact(content="Content 2", tags=["test", "important"])
    mock_memory.recall.return_value = [artifact1, artifact2]
    
    # Run tool
    result = await recall_tool.run(
        query="test content",
        limit=10,
        tags=["test"]
    )
    
    # Verify mock was called correctly
    mock_memory.recall.assert_called_once_with("test content", limit=10, tags=["test"])
    
    # Verify result
    assert result["success"] is True
    assert result["query"] == "test content"
    assert result["results_count"] == 2
    assert len(result["results"]) == 2
    
    # Check first result structure
    first_result = result["results"][0]
    assert first_result["id"] == str(artifact1.id)
    assert first_result["content"] == "Content 1"
    assert first_result["tags"] == ["test"]
    assert "created_at" in first_result
    assert first_result["metadata"] == {}


@pytest.mark.asyncio
async def test_recall_tool_run_missing_query(recall_tool):
    """Test recall tool with missing query parameter."""
    result = await recall_tool.run()
    
    assert "error" in result
    assert "query parameter is required" in result["error"]


@pytest.mark.asyncio
async def test_recall_tool_run_with_defaults(recall_tool, mock_memory):
    """Test recall tool with default parameters."""
    mock_memory.recall.return_value = []
    
    result = await recall_tool.run(query="test")
    
    mock_memory.recall.assert_called_once_with("test", limit=None, tags=None)
    assert result["success"] is True
    assert result["results_count"] == 0


@pytest.mark.asyncio
async def test_recall_tool_run_exception(recall_tool, mock_memory):
    """Test recall tool handling exceptions."""
    mock_memory.recall.side_effect = Exception("Memory error")
    
    result = await recall_tool.run(query="test")
    
    assert "error" in result
    assert "Failed to recall content" in result["error"]


@pytest.mark.asyncio
async def test_recall_tool_empty_tags_handling(recall_tool, mock_memory):
    """Test recall tool with empty tags list."""
    mock_memory.recall.return_value = []
    
    result = await recall_tool.run(query="test", tags=[])
    
    # Empty tags should be converted to None
    mock_memory.recall.assert_called_once_with("test", limit=None, tags=None)


def test_memorize_tool_schema(memorize_tool):
    """Test MemorizeTool schema generation."""
    schema_str = memorize_tool.get_schema()
    schema = json.loads(schema_str)
    
    assert schema["name"] == "memorize"
    assert "content" in schema["parameters"]["properties"]
    assert "tags" in schema["parameters"]["properties"]
    assert "metadata" in schema["parameters"]["properties"]
    assert schema["parameters"]["required"] == ["content"]


def test_recall_tool_schema(recall_tool):
    """Test RecallTool schema generation."""
    schema_str = recall_tool.get_schema()
    schema = json.loads(schema_str)
    
    assert schema["name"] == "recall"
    assert "query" in schema["parameters"]["properties"]
    assert "limit" in schema["parameters"]["properties"]
    assert "tags" in schema["parameters"]["properties"]
    assert schema["parameters"]["required"] == ["query"]


def test_memorize_tool_usage_examples(memorize_tool):
    """Test MemorizeTool usage examples."""
    examples = memorize_tool.get_usage_examples()
    
    assert len(examples) > 0
    for example in examples:
        assert "memorize(" in example
        assert "content=" in example


def test_recall_tool_usage_examples(recall_tool):
    """Test RecallTool usage examples."""
    examples = recall_tool.get_usage_examples()
    
    assert len(examples) > 0
    for example in examples:
        assert "recall(" in example
        assert "query=" in example