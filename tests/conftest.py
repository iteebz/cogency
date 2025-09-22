"""Essential test machinery - WebSocket mocking and async generators."""

import pytest


async def get_agent_response(agent, query, **kwargs):
    """Helper to extract final response from agent stream - maintains test compatibility."""
    response_content = ""
    async for event in agent(query, **kwargs):
        if event["type"] == "respond":
            response_content += event["content"]
    return response_content.strip()


pytest_plugins = ["pytest_asyncio"]


def mock_generator(items):
    """Fresh async generator per call - eliminates dead coroutine ceremony."""

    async def async_gen():
        for item in items:
            yield item

    return lambda *args, **kwargs: async_gen()


@pytest.fixture
def mock_llm():
    """Universal LLM mock with streaming, WebSocket, and customizable response support."""
    import asyncio
    from unittest.mock import AsyncMock

    from cogency.core.protocols import LLM

    class MockLLM(LLM):
        http_model = "gpt-4"  # For token counting with tiktoken
        resumable = False

        def __init__(self, response_tokens=None):
            self.response_tokens = response_tokens or ["§respond: Test response\n", "§end\n"]
            self._is_session = False
            self.generate = AsyncMock(return_value="Test response")

        def set_response_tokens(self, tokens: list[str]):
            """Dynamically set response tokens for streaming."""
            self.response_tokens = tokens
            return self

        async def connect(self, messages):
            """WebSocket session creation."""
            session_instance = MockLLM(self.response_tokens)
            session_instance._is_session = True
            return session_instance

        async def stream(self, messages):
            """HTTP streaming with full conversation context."""
            for token in self.response_tokens:
                yield token
                await asyncio.sleep(0.001)  # Simulate async streaming

        async def send(self, content):
            """Send message in WebSocket session and stream response."""
            if not self._is_session:
                raise RuntimeError("send() requires active session. Call connect() first.")

            for token in self.response_tokens:
                yield token
                await asyncio.sleep(0.001)

        async def receive(self, session):
            """Legacy WebSocket receive method."""
            yield "token1"
            yield "token2"

        async def close(self):
            """Close WebSocket session."""
            self._is_session = False
            return True

    return MockLLM()


@pytest.fixture
def mock_storage():
    """Mutable storage test double."""

    class TestStorage:
        def __init__(self):
            self.messages = []
            self.profiles = {}
            self.base_dir = None

        async def save_message(self, conversation_id, user_id, msg_type, content, timestamp=None):
            self.messages.append(
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "type": msg_type,
                    "content": content,
                    "timestamp": timestamp,
                }
            )

        async def load_messages(self, conversation_id, include=None, exclude=None):
            return [msg for msg in self.messages if msg["conversation_id"] == conversation_id]

        async def save_profile(self, user_id, profile):
            self.profiles[user_id] = profile

        async def load_profile(self, user_id):
            return self.profiles.get(user_id, {})

        async def count_user_messages(self, user_id, since_timestamp=0):
            """Count user messages since timestamp."""
            count = 0
            for msg in self.messages:
                if msg["user_id"] == user_id and msg.get("timestamp", 0) > since_timestamp:
                    count += 1
            return count

    return TestStorage()


@pytest.fixture
def mock_config(mock_llm, mock_storage):
    """Mutable config test double - NOT frozen production Config."""

    class TestConfig:
        def __init__(self, llm, storage):
            from cogency.core.config import Security

            # Capabilities
            self.llm = llm
            self.storage = storage
            self.tools = []

            # User steering layer
            self.instructions = None

            # Execution behavior
            self.max_iterations = 3
            self.mode = "auto"
            self.profile = True
            self.learn_every = 5
            self.history_window = 20
            self.security = Security()

    return TestConfig(mock_llm, mock_storage)


@pytest.fixture
def mock_tool():
    """Universal tool mock that can be customized for different test scenarios."""
    from cogency.core.protocols import Tool, ToolResult

    class MockTool(Tool):
        """Universal tool for testing."""

        def __init__(
            self, name="test_tool", description="Tool for testing", schema=None, should_fail=False
        ):
            self._name = name
            self._description = description
            self._schema = schema or {"message": {}}
            self._should_fail = should_fail

        @property
        def name(self) -> str:
            return self._name

        @property
        def description(self) -> str:
            return self._description

        @property
        def schema(self) -> dict:
            return self._schema

        def describe(self, args: dict) -> str:
            return f"Executing {self._name} with {args}"

        def configure(self, name=None, description=None, schema=None, should_fail=None):
            """Dynamically configure the mock tool."""
            if name is not None:
                self._name = name
            if description is not None:
                self._description = description
            if schema is not None:
                self._schema = schema
            if should_fail is not None:
                self._should_fail = should_fail
            return self

        async def execute(self, message: str = "default", **kwargs):
            if self._should_fail:
                raise RuntimeError("Tool execution failed")
            return ToolResult(
                outcome=f"Tool executed: {message}", content=f"Full details: {message}"
            )

    return MockTool()
