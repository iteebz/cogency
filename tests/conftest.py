from unittest.mock import AsyncMock, Mock

import pytest

from cogency.core.protocols import LLM, Tool, ToolResult


class TestStorage:
    def __init__(self):
        self.messages = []
        self.events = []
        self.requests = []
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

    async def save_event(self, conversation_id, msg_type, content, timestamp=None):
        self.events.append(
            {
                "conversation_id": conversation_id,
                "type": msg_type,
                "content": content,
                "timestamp": timestamp,
            }
        )

    async def save_request(self, conversation_id, user_id, messages, response=None, timestamp=None):
        self.requests.append(
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "messages": messages,
                "response": response,
                "timestamp": timestamp,
            }
        )

    async def load_messages(
        self, conversation_id, user_id=None, include=None, exclude=None, limit=None
    ):
        messages = [
            msg
            for msg in self.messages
            if msg["conversation_id"] == conversation_id
            and (user_id is None or msg.get("user_id") == user_id)
        ]
        if limit is not None:
            messages = messages[-limit:]
        return messages

    async def save_profile(self, user_id, profile):
        self.profiles[user_id] = profile

    async def load_profile(self, user_id):
        return self.profiles.get(user_id, {})

    async def count_user_messages(self, user_id, since_timestamp=0):
        count = 0
        for msg in self.messages:
            if msg["user_id"] == user_id and msg.get("timestamp", 0) > since_timestamp:
                count += 1
        return count


async def get_agent_response(agent, query, **kwargs):
    response_content = ""
    async for event in agent(query, **kwargs):
        if event["type"] == "respond":
            response_content += event["content"]
    return response_content.strip()


pytest_plugins = ["pytest_asyncio"]


def mock_generator(items):
    async def async_gen():
        for item in items:
            yield item

    return lambda *args, **kwargs: async_gen()


@pytest.fixture
def mock_llm():
    import asyncio

    class MockLLM(LLM):
        http_model = "gpt-4"  # For token counting with tiktoken
        resumable = False

        def __init__(self, response_tokens=None):
            self.response_tokens = response_tokens or ["<respond>Test response</respond>"]
            self._is_session = False
            self.generate = AsyncMock(return_value="Test response")
            self._continuation_error = None

        def set_response_tokens(self, tokens: list[str]):
            self.response_tokens = tokens
            return self

        def set_continuation_error(self, error: Exception):
            self._continuation_error = error
            return self

        async def connect(self, messages):
            session_instance = MockLLM(self.response_tokens)
            session_instance._is_session = True
            session_instance._continuation_error = self._continuation_error  # Pass error to session
            return session_instance

        async def stream(self, messages):
            for token in self.response_tokens:
                yield token
                await asyncio.sleep(0.001)  # Simulate async streaming

        async def send(self, content):
            if not self._is_session:
                raise RuntimeError("send() requires active session. Call connect() first.")

            for token in self.response_tokens:
                yield token
                await asyncio.sleep(0.001)  # Simulate async streaming

            if self._continuation_error:
                raise self._continuation_error

        async def receive(self, session):
            yield "token1"
            yield "token2"

        async def close(self):
            self._is_session = False

    return MockLLM()


@pytest.fixture
def mock_storage():
    return TestStorage()


@pytest.fixture
def failing_storage():
    class FailingStorage(TestStorage):
        async def save_message(self, *args, **kwargs):
            raise RuntimeError("Storage write failed")

    return FailingStorage()


@pytest.fixture
def mock_config(mock_llm, mock_storage):
    class TestConfig:
        def __init__(self, llm, storage):
            from cogency.core.config import Execution, Security

            # Capabilities
            self.llm = llm
            self.storage = storage
            self.tools = []
            # User steering layer
            self.identity = None
            self.instructions = None

            # Execution behavior
            self.max_iterations = 3
            self.mode = "auto"
            self.profile = False
            self.history_window = 20
            self.history_transform = None
            self.security = Security()
            self.debug = False
            self.notifications = None

            self._execution_cls = Execution

        @property
        def execution(self):
            return self._execution_cls(
                storage=self.storage,
                tools=tuple(self.tools),
                shell_timeout=self.security.shell_timeout,
                sandbox_dir=self.security.sandbox_dir,
                access=self.security.access,
            )

    return TestConfig(mock_llm, mock_storage)


@pytest.fixture
def mock_stream_context():
    mock_context = Mock()
    mock_context.telemetry_events = []
    mock_context.metrics = Mock()
    mock_context.complete = False
    return mock_context


@pytest.fixture
def mock_tool():
    class MockTool(Tool):
        name = "test_tool"
        description = "Tool for testing"
        schema = {"message": {}}

        def __init__(
            self, name="test_tool", description="Tool for testing", schema=None, should_fail=False
        ):
            self.name = name
            self.description = description
            self.schema = schema or {"message": {}}
            self._should_fail = should_fail

        def describe(self, args: dict) -> str:
            return f"{self.name}({', '.join(f'{k}={v}' for k, v in args.items())})"

        def configure(self, name=None, description=None, schema=None, should_fail=None):
            if name is not None:
                self.name = name
            if description is not None:
                self.description = description
            if schema is not None:
                self.schema = schema
            if should_fail is not None:
                self._should_fail = should_fail
            return self

        async def execute(self, message: str = "default", **kwargs):
            if self._should_fail:
                raise RuntimeError("Tool execution failed")
            return ToolResult(
                outcome=f"Tool executed: {message}", content=f"Full details: {message}"
            )

    return MockTool


class _ResumeSessionMock:
    def __init__(self, turns: list[list[str]]):
        self._turns = [list(turn) for turn in turns]
        self._index = 0

    async def send(self, _content):
        tokens = self._turns[self._index] if self._index < len(self._turns) else []
        self._index += 1
        for token in tokens:
            yield token

    async def close(self):
        pass


class _ResumeLLMMock:
    http_model = "seq-llm"

    def __init__(self, turns: list[list[str]]):
        self._turns = [list(turn) for turn in turns]

    async def connect(self, _messages):
        return _ResumeSessionMock(self._turns)


@pytest.fixture
def resume_llm():
    def factory(turns: list[list[str]]):
        return _ResumeLLMMock(turns)

    return factory
