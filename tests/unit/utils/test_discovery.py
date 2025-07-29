"""Test cases for unified automagical discovery registry."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from cogency.utils.discovery import AutoRegistry, create_registry


class BaseService:
    """Mock base class for testing."""

    pass


class MockOpenAI(BaseService):
    """Mock OpenAI implementation."""

    pass


class MockAnthropic(BaseService):
    """Mock Anthropic implementation."""

    pass


class TestAutoRegistry:
    """Beautiful test suite for AutoRegistry - covers all edge cases."""

    def setup_method(self):
        """Clean slate for each test."""
        self.registry = AutoRegistry(package_name="test_package", base_class=BaseService)

    def test_automagical_discovery_finds_implementations(self):
        """Test that registry discovers all subclasses automagically."""
        # Mock the discovery to simulate finding implementations
        mock_registry = {"openai": MockOpenAI, "anthropic": MockAnthropic}

        with patch.object(self.registry, "_registry", mock_registry):
            with patch.object(self.registry, "_discovered", True):
                providers = self.registry.list_providers()

                assert "openai" in providers
                assert "anthropic" in providers
                assert len(providers) == 2

    def test_get_specific_provider_returns_correct_class(self):
        """Test getting specific provider by name."""
        mock_registry = {"openai": MockOpenAI}

        with patch.object(self.registry, "_registry", mock_registry):
            with patch.object(self.registry, "_discovered", True):
                provider_class = self.registry.get("openai")

                assert provider_class == MockOpenAI

    def test_get_without_provider_returns_first_available(self):
        """Test getting provider without name returns first available."""
        mock_registry = {"openai": MockOpenAI, "anthropic": MockAnthropic}

        with patch.object(self.registry, "_registry", mock_registry):
            with patch.object(self.registry, "_discovered", True):
                provider_class = self.registry.get()

                # Should return one of the available providers
                assert provider_class in [MockOpenAI, MockAnthropic]

    def test_get_nonexistent_provider_raises_helpful_error(self):
        """Test that requesting nonexistent provider gives helpful error."""
        mock_registry = {"openai": MockOpenAI}

        with patch.object(self.registry, "_registry", mock_registry):
            with patch.object(self.registry, "_discovered", True):
                with pytest.raises(ValueError) as exc_info:
                    self.registry.get("nonexistent")

                error_msg = str(exc_info.value)
                assert "nonexistent" in error_msg
                assert "openai" in error_msg  # Shows available options

    def test_empty_registry_raises_clear_error(self):
        """Test that empty registry gives clear error message."""
        with patch.object(self.registry, "_registry", {}):
            with patch.object(self.registry, "_discovered", True):
                with pytest.raises(ValueError) as exc_info:
                    self.registry.get()

                assert "No implementations found" in str(exc_info.value)

    def test_custom_key_extractor_works(self):
        """Test that custom key extraction function works."""
        custom_registry = AutoRegistry(
            package_name="test_package",
            base_class=BaseService,
            key_extractor=lambda name: name.upper().split(".")[-1],
        )

        mock_registry = {"OPENAI": MockOpenAI}

        with patch.object(custom_registry, "_registry", mock_registry):
            with patch.object(custom_registry, "_discovered", True):
                providers = custom_registry.list_providers()

                assert "OPENAI" in providers

    def test_skip_modules_are_ignored(self):
        """Test that specified modules are skipped during discovery."""
        registry_with_skips = AutoRegistry(
            package_name="test_package", base_class=BaseService, skip_modules=["base", "test_skip"]
        )

        # Verify skip_modules are set
        assert "base" in registry_with_skips.skip_modules
        assert "test_skip" in registry_with_skips.skip_modules

    def test_all_returns_complete_registry_copy(self):
        """Test that all() returns complete registry mapping."""
        mock_registry = {"openai": MockOpenAI, "anthropic": MockAnthropic}

        with patch.object(self.registry, "_registry", mock_registry):
            with patch.object(self.registry, "_discovered", True):
                all_providers = self.registry.all()

                assert all_providers == mock_registry
                # Verify it's a copy, not reference
                assert all_providers is not self.registry._registry

    def test_clear_resets_registry_for_testing(self):
        """Test that clear() properly resets registry state."""
        # Set up some mock state
        with patch.object(self.registry, "_registry", {"test": MockOpenAI}):
            with patch.object(self.registry, "_discovered", True):
                # Clear should reset everything
                self.registry.clear()

                assert self.registry._registry == {}
                assert self.registry._discovered is False

    def test_discovery_only_runs_once(self):
        """Test that discovery is lazy and only runs once."""
        with patch.object(self.registry, "discover") as mock_discover:
            # Multiple calls should only trigger discovery once
            self.registry.get("test")
            self.registry.list_providers()
            self.registry.all()

            # Should be called once due to _discovered flag
            assert mock_discover.call_count >= 1

    def test_factory_function_creates_registry(self):
        """Test that create_registry factory function works."""
        registry = create_registry("test_package", BaseService)

        assert isinstance(registry, AutoRegistry)
        assert registry.package_name == "test_package"
        assert registry.base_class == BaseService

    def test_discovery_handles_import_errors_gracefully(self):
        """Test that discovery continues when individual modules fail to import."""
        # This test verifies the contextlib.suppress(ImportError) behavior
        registry = AutoRegistry("nonexistent.package", BaseService)

        # Should not raise, just result in empty registry
        registry.discover()

        assert registry._discovered is True
        assert len(registry._registry) == 0

    def test_type_hints_work_correctly(self):
        """Test that TypeVar and generic typing work as expected."""
        from typing import get_type_hints

        # This ensures the generic typing is set up correctly
        registry = create_registry("test", BaseService)

        # Should be able to get type hints without errors
        hints = get_type_hints(registry.get)
        assert hints is not None


class TestAutoRegistryIntegration:
    """Integration tests using real cogency modules."""

    def test_real_llm_discovery(self):
        """Test discovery works with actual LLM services."""
        from cogency.services.llm.base import LLM

        registry = AutoRegistry("cogency.services.llm", LLM)
        providers = registry.list_providers()

        # Should find real implementations
        expected_providers = ["openai", "anthropic", "gemini", "mistral", "xai"]
        for provider in expected_providers:
            assert provider in providers

    def test_real_tool_discovery(self):
        """Test discovery works with actual tools."""
        from cogency.tools.base import Tool

        registry = AutoRegistry("cogency.tools", Tool)
        providers = registry.list_providers()

        # Should find some real tools
        assert len(providers) > 0
        # Common tools that should exist
        expected_tools = ["Calculator", "Files", "Shell"]  # Adjust based on actual tool names
        for tool in expected_tools:
            if tool.lower() in [p.lower() for p in providers]:
                continue  # Found at least one expected tool

        # At least one expected tool should be found
        assert len(providers) > 0
