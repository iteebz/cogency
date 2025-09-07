"""Unit tests for Gemini provider - WebSocket specific logic."""

from cogency.lib.llms.gemini import Gemini


class TestGeminiWebSocketConfig:
    """Test Gemini Live WebSocket config preparation logic."""

    def setup_method(self):
        """Set up test instance."""
        self.gemini = Gemini()

    def test_system_instructions_in_config(self):
        """System messages should go into systemInstruction parameter."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello world"},
        ]

        config, user_messages = self.gemini._prepare_websocket_config(messages)

        assert "systemInstruction" in config
        assert "parts" in config["systemInstruction"]
        assert len(config["systemInstruction"]["parts"]) == 1
        assert "text" in config["systemInstruction"]["parts"][0]
        assert "You are a helpful assistant." in config["systemInstruction"]["parts"][0]["text"]

        assert len(user_messages) == 1
        assert user_messages[0]["role"] == "user"
        assert user_messages[0]["content"] == "Hello world"

    def test_multiple_system_messages_combined(self):
        """Multiple system messages should be combined in systemInstruction."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Help me"},
        ]

        config, user_messages = self.gemini._prepare_websocket_config(messages)

        system_text = config["systemInstruction"]["parts"][0]["text"]
        assert "You are helpful." in system_text
        assert "Be concise." in system_text

        assert len(user_messages) == 1
        assert user_messages[0]["content"] == "Help me"

    def test_only_system_messages(self):
        """Only system messages should result in systemInstruction but empty user messages."""
        messages = [{"role": "system", "content": "You are helpful."}]

        config, user_messages = self.gemini._prepare_websocket_config(messages)

        assert "systemInstruction" in config
        assert "You are helpful." in config["systemInstruction"]["parts"][0]["text"]
        assert len(user_messages) == 0

    def test_only_user_messages(self):
        """User-only messages should be returned without systemInstruction."""
        messages = [{"role": "user", "content": "Hello"}, {"role": "user", "content": "World"}]

        config, user_messages = self.gemini._prepare_websocket_config(messages)

        assert "systemInstruction" not in config
        assert len(user_messages) == 2
        assert user_messages[0] == {"role": "user", "content": "Hello"}
        assert user_messages[1] == {"role": "user", "content": "World"}

    def test_includes_all_non_system_roles(self):
        """Non-system roles should all be included in user messages."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant response"},
            {"role": "model", "content": "Model response"},
        ]

        config, user_messages = self.gemini._prepare_websocket_config(messages)

        # System goes to systemInstruction
        assert "System prompt" in config["systemInstruction"]["parts"][0]["text"]

        # All other roles go to user_messages
        assert len(user_messages) == 3
        assert user_messages[0]["role"] == "user"
        assert user_messages[0]["content"] == "User message"
        assert user_messages[1]["role"] == "assistant"
        assert user_messages[1]["content"] == "Assistant response"
        assert user_messages[2]["role"] == "model"
        assert user_messages[2]["content"] == "Model response"

    def test_config_has_response_settings(self):
        """The config should include response settings."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
        ]

        config, _ = self.gemini._prepare_websocket_config(messages)

        # Check config has response settings
        assert "response_modalities" in config
        assert "max_output_tokens" in config

    def test_empty_messages_list(self):
        """Empty message list should return config without systemInstruction and empty user messages."""
        config, user_messages = self.gemini._prepare_websocket_config([])
        assert "systemInstruction" not in config
        assert len(user_messages) == 0
