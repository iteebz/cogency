"""Integration tests for memory system E2E functionality."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency import Agent
from cogency.knowledge import KnowledgeArtifact
from cogency.memory import Profile
from cogency.storage import SQLite


@pytest.fixture
async def memory_agent():
    """Create agent with memory enabled for testing."""
    # Mock providers to avoid external dependencies
    mock_llm = AsyncMock()
    mock_embed = AsyncMock()

    # Setup successful LLM responses
    mock_llm.generate.return_value = Result.ok('{"reasoning": "test", "response": "Test response"}')

    # Setup successful embedding responses
    mock_embed.embed.return_value = Result.ok([[0.1] * 768])

    agent = Agent("test", memory=True)
    agent.llm = mock_llm
    agent.embed = mock_embed

    return agent


@pytest.fixture
async def sample_profile():
    """Create sample user profile for testing."""
    return Profile(
        user_id="test_user",
        preferences={"coding_style": "functional", "language": "python"},
        goals=["learn machine learning", "build AI systems"],
        expertise_areas=["python", "data science"],
        communication_style="concise and technical",
    )


class TestMemoryIntegration:
    """Test end-to-end memory system integration."""

    async def test_automatic_knowledge_retrieval_in_reasoning(self, memory_agent):
        """Test that reasoning automatically queries knowledge without explicit calls."""
        # Setup knowledge in memory first
        store = SQLite()
        await store._ensure_schema()

        knowledge = KnowledgeArtifact(
            topic="Python Best Practices",
            content="Use list comprehensions for better performance. Avoid global variables.",
            confidence=0.9,
            user_id="test_user",
        )

        await store.save_knowledge(knowledge)

        # Mock successful embedding lookup
        memory_agent.embed.embed.return_value = Result.ok([[0.1] * 768])

        # Query that should trigger knowledge retrieval
        query = "What are some Python performance tips?"

        # Mock reasoning to capture context
        captured_context = None

        async def capture_context(*args, **kwargs):
            nonlocal captured_context
            # Context should be in the prompt
            if len(args) > 0:
                captured_context = args[0][0]["content"]  # First message content
            return Result.ok('{"reasoning": "Found tips", "response": "Use list comprehensions"}')

        memory_agent.llm.generate.side_effect = capture_context

        # Execute query
        await memory_agent.run_async(query, user_id="test_user")

        # Verify knowledge was automatically retrieved and included in context
        assert captured_context is not None
        assert "RELEVANT KNOWLEDGE:" in captured_context
        assert "Python Best Practices" in captured_context
        assert "list comprehensions" in captured_context

    async def test_profile_context_injection(self, memory_agent, sample_profile):
        """Test that user profile context is automatically injected into reasoning."""
        # Save profile to storage
        store = SQLite()
        await store._ensure_schema()
        await store.save_profile("test_user:default", sample_profile)

        captured_context = None

        async def capture_context(*args, **kwargs):
            nonlocal captured_context
            if len(args) > 0:
                captured_context = args[0][0]["content"]
            return Result.ok('{"reasoning": "Understood", "response": "Python advice"}')

        memory_agent.llm.generate.side_effect = capture_context

        # Execute query
        await memory_agent.run_async("Help me with coding", user_id="test_user")

        # Verify profile context was injected
        assert captured_context is not None
        assert "USER CONTEXT:" in captured_context
        assert "functional" in captured_context  # coding_style preference
        assert "python" in captured_context  # expertise area
        assert "machine learning" in captured_context  # goal

    async def test_conversation_filtering_prevents_extraction(self, memory_agent):
        """Test that simple conversations don't trigger knowledge extraction."""
        # Mock successful responses
        memory_agent.llm.generate.return_value = Result.ok(
            '{"reasoning": "Simple greeting", "response": "Hello!"}'
        )

        # Simple greeting that shouldn't trigger extraction
        result = await memory_agent.run_async("Hello", user_id="test_user")

        # Verify no knowledge extraction occurred (would be in call logs)
        # Knowledge extraction would involve additional LLM calls beyond reasoning
        llm_calls = memory_agent.llm.generate.call_count

        # Should only have 1 call for reasoning, not additional for extraction
        assert llm_calls == 1
        assert "Hello" in result or "Hi" in result

    async def test_substantial_conversation_triggers_extraction(self, memory_agent):
        """Test that substantial conversations trigger knowledge extraction."""
        # Mock extraction prompt response
        extraction_response = """
        {
            "knowledge": [
                {
                    "topic": "API Design",
                    "knowledge": "RESTful APIs should use HTTP methods semantically",
                    "confidence": 0.85,
                    "context": "web development"
                }
            ]
        }
        """

        # Setup LLM to handle both reasoning and extraction
        responses = [
            Result.ok(
                '{"reasoning": "Complex API question", "response": "RESTful APIs use HTTP methods..."}'
            ),
            Result.ok(extraction_response),  # For knowledge extraction
        ]
        memory_agent.llm.generate.side_effect = responses

        # Complex query that should trigger extraction
        query = "How should I design REST APIs for maximum scalability and maintainability?"
        await memory_agent.run_async(query, user_id="test_user")

        # Verify both reasoning and extraction calls occurred
        assert memory_agent.llm.generate.call_count == 2

        # Verify knowledge was extracted and stored
        store = SQLite()
        knowledge_items = await store.search_knowledge("API Design", user_id="test_user", top_k=1)
        assert len(knowledge_items) > 0
        assert "RESTful" in knowledge_items[0].content

    async def test_merge_quality_validation(self, memory_agent):
        """Test that merge quality validation prevents poor merges."""
        store = SQLite()
        await store._ensure_schema()

        # Add initial knowledge
        existing = KnowledgeArtifact(
            topic="Testing",
            content="Unit tests verify individual components work correctly.",
            confidence=0.9,
            user_id="test_user",
        )
        await store.save_knowledge(existing)

        # Mock poor quality merge (just concatenation)
        poor_merge = "Unit tests verify individual components work correctly. Integration tests check component interactions."

        memory_agent.llm.generate.side_effect = [
            Result.ok('{"reasoning": "Testing question", "response": "Integration tests..."}'),
            Result.ok(
                """{"knowledge": [{"topic": "Testing", "knowledge": "Integration tests check component interactions.", "confidence": 0.8}]}"""
            ),
            Result.ok(poor_merge),  # Poor merge result
        ]

        # Query that would trigger merge
        await memory_agent.run_async("What are integration tests?", user_id="test_user")

        # Check that poor merge was rejected (original should remain unchanged)
        knowledge_items = await store.search_knowledge("Testing", user_id="test_user", top_k=2)

        # Should have 2 separate items, not a merged one
        assert len(knowledge_items) == 2
        # Original should still exist unchanged
        contents = [item.content for item in knowledge_items]
        assert any("Unit tests verify individual" in content for content in contents)

    async def test_simple_query_skips_retrieval(self, memory_agent):
        """Test that simple queries don't trigger knowledge retrieval."""
        captured_context = None

        async def capture_context(*args, **kwargs):
            nonlocal captured_context
            if len(args) > 0:
                captured_context = args[0][0]["content"]
            return Result.ok('{"reasoning": "Simple question", "response": "I\'m fine, thanks!"}')

        memory_agent.llm.generate.side_effect = capture_context

        # Simple question that shouldn't trigger retrieval
        await memory_agent.run_async("How are you?", user_id="test_user")

        # Context should not contain "RELEVANT KNOWLEDGE" section
        assert captured_context is not None
        assert "RELEVANT KNOWLEDGE:" not in captured_context

    async def test_memory_system_end_to_end_flow(self, memory_agent, sample_profile):
        """Test complete memory system flow: profile + knowledge + extraction + retrieval."""
        store = SQLite()
        await store._ensure_schema()
        await store.save_profile("test_user:default", sample_profile)

        # Add some existing knowledge
        existing_knowledge = KnowledgeArtifact(
            topic="Machine Learning",
            content="Neural networks require large datasets for effective training.",
            confidence=0.9,
            user_id="test_user",
        )
        await store.save_knowledge(existing_knowledge)

        # Mock responses for complex ML question
        responses = [
            Result.ok(
                '{"reasoning": "ML architecture question", "response": "For deep learning, consider transformer architectures..."}'
            ),
            Result.ok(
                '{"knowledge": [{"topic": "Deep Learning", "knowledge": "Transformers use attention mechanisms", "confidence": 0.85}]}'
            ),
        ]
        memory_agent.llm.generate.side_effect = responses

        captured_context = None

        async def capture_context(*args, **kwargs):
            nonlocal captured_context
            if len(args) > 0:
                captured_context = args[0][0]["content"]
            return (
                responses.pop(0)
                if responses
                else Result.ok('{"reasoning": "Done", "response": "Complete"}')
            )

        memory_agent.llm.generate.side_effect = capture_context

        # Complex query that exercises full memory system
        query = "What deep learning architecture should I use for my ML project?"
        await memory_agent.run_async(query, user_id="test_user")

        # Verify all memory components were activated:
        assert captured_context is not None

        # 1. Profile context injection
        assert "USER CONTEXT:" in captured_context
        assert "machine learning" in captured_context  # from user goals

        # 2. Knowledge retrieval
        assert "RELEVANT KNOWLEDGE:" in captured_context
        assert "Neural networks" in captured_context  # from existing knowledge

        # 3. Knowledge extraction should have occurred (additional LLM call)
        # 4. New knowledge should be stored
        new_knowledge = await store.search_knowledge("Deep Learning", user_id="test_user", top_k=1)
        assert len(new_knowledge) > 0
        assert "Transformers" in new_knowledge[0].content


@pytest.mark.integration
class TestMemorySystemRobustness:
    """Test memory system robustness and error handling."""

    async def test_memory_system_handles_llm_failures(self, memory_agent):
        """Test that memory system gracefully handles LLM failures."""
        # Mock LLM failure for reasoning
        memory_agent.llm.generate.return_value = Result.fail("LLM service unavailable")

        # Should not crash, should return error message
        result = await memory_agent.run_async("Test query", user_id="test_user")

        assert "Error:" in result
        assert "LLM service unavailable" in result

    async def test_memory_system_handles_storage_failures(self, memory_agent):
        """Test that memory system handles storage failures gracefully."""
        # Mock storage failure by using invalid database path
        original_db_path = SQLite().db_path
        SQLite().db_path = "/invalid/path/database.db"

        try:
            # Should not crash on storage errors
            result = await memory_agent.run_async("Test query", user_id="test_user")
            # Should still provide response even if memory operations fail
            assert result is not None
        finally:
            # Restore original path
            SQLite().db_path = original_db_path
