"""Tests for CLI interface and entry points."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogency.cli import interactive_mode, main


@pytest.mark.asyncio
async def test_interactive_mode_basic():
    """Test interactive mode basic functionality."""
    mock_agent = AsyncMock()
    mock_agent.run_async.return_value = "Test response"

    with patch("builtins.input", side_effect=["test message", "exit"]):
        with patch("builtins.print") as mock_print:
            await interactive_mode(mock_agent)
            mock_agent.run_async.assert_called_once_with("test message")
            mock_print.assert_called()


@pytest.mark.asyncio
async def test_interactive_mode_quit():
    """Test interactive mode quit command."""
    mock_agent = AsyncMock()

    with patch("builtins.input", side_effect=["quit"]):
        with patch("builtins.print"):
            await interactive_mode(mock_agent)
            mock_agent.run_async.assert_not_called()


@pytest.mark.asyncio
async def test_interactive_mode_keyboard_interrupt():
    """Test interactive mode keyboard interrupt handling."""
    mock_agent = AsyncMock()

    with patch("builtins.input", side_effect=KeyboardInterrupt):
        with patch("builtins.print") as mock_print:
            await interactive_mode(mock_agent)
            mock_agent.run_async.assert_not_called()
            # Should print goodbye message
            assert any("Goodbye" in str(call) for call in mock_print.call_args_list)


@pytest.mark.asyncio
async def test_interactive_mode_eof():
    """Test interactive mode EOF handling."""
    mock_agent = AsyncMock()

    with patch("builtins.input", side_effect=EOFError):
        with patch("builtins.print"):
            await interactive_mode(mock_agent)
            mock_agent.run_async.assert_not_called()


@pytest.mark.asyncio
async def test_interactive_mode_empty_message():
    """Test interactive mode skips empty messages."""
    mock_agent = AsyncMock()

    with patch("builtins.input", side_effect=["", "  ", "exit"]):
        with patch("builtins.print"):
            await interactive_mode(mock_agent)
            mock_agent.run_async.assert_not_called()


@pytest.mark.asyncio
async def test_interactive_mode_error_handling():
    """Test interactive mode error handling."""
    mock_agent = AsyncMock()
    mock_agent.run_async.side_effect = Exception("Agent error")

    with patch("builtins.input", side_effect=["test", "exit"]):
        with patch("builtins.print") as mock_print:
            await interactive_mode(mock_agent)
            # Should print error message
            assert any("Error:" in str(call) for call in mock_print.call_args_list)


def test_main_version():
    """Test CLI version argument."""
    with patch("sys.argv", ["cogency", "--version"]):
        with pytest.raises(SystemExit):
            main()


def test_main_help():
    """Test CLI help argument."""
    with patch("sys.argv", ["cogency", "--help"]):
        with pytest.raises(SystemExit):
            main()


def test_main_single_message():
    """Test CLI single message mode."""
    with patch("sys.argv", ["cogency", "hello", "world"]):
        with patch("cogency.Agent") as mock_agent_class:
            with patch("asyncio.run") as mock_run:
                mock_agent = MagicMock()
                mock_agent_class.return_value = mock_agent

                main()

                # Should create agent with tools and memory
                mock_agent_class.assert_called_once()
                args, kwargs = mock_agent_class.call_args
                assert args[0] == "assistant"
                assert len(kwargs["tools"]) > 0  # Should have tools
                assert kwargs["memory"] is True

                # Should run in single message mode
                mock_run.assert_called_once()


def test_main_interactive_flag():
    """Test CLI interactive flag."""
    with patch("sys.argv", ["cogency", "-i"]):
        with patch("cogency.Agent") as mock_agent_class:
            with patch("asyncio.run") as mock_run:
                with patch("cogency.cli.interactive_mode"):
                    mock_agent = MagicMock()
                    mock_agent_class.return_value = mock_agent

                    main()

                    # Should run interactive mode
                    mock_run.assert_called_once()


def test_main_no_args_interactive():
    """Test CLI defaults to interactive when no message."""
    with patch("sys.argv", ["cogency"]):
        with patch("cogency.Agent") as mock_agent_class:
            with patch("asyncio.run") as mock_run:
                mock_agent = MagicMock()
                mock_agent_class.return_value = mock_agent

                main()

                # Should default to interactive mode
                mock_run.assert_called_once()


def test_main_with_retrieval_env():
    """Test CLI with retrieval environment variable."""
    with patch("sys.argv", ["cogency", "test"]):
        with patch.dict("os.environ", {"COGENCY_RETRIEVAL_PATH": "/test/path"}):
            with patch("cogency.Agent") as mock_agent_class:
                with patch("asyncio.run"):
                    with patch("cogency.tools.Retrieve") as mock_retrieval:
                        mock_agent = MagicMock()
                        mock_agent_class.return_value = mock_agent

                        main()

                        # Should create Retrieve tool
                        mock_retrieval.assert_called_once()

                        # Should include Retrieval in tools
                        args, kwargs = mock_agent_class.call_args
                        assert len(kwargs["tools"]) > 5  # Base tools + Retrieval


def test_main_agent_creation_error():
    """Test CLI handles agent creation errors."""
    with patch("sys.argv", ["cogency", "test"]):
        with patch("cogency.Agent", side_effect=Exception("Agent creation failed")):
            with patch("builtins.print") as mock_print:
                with patch("sys.exit") as mock_exit:
                    # Mock sys.exit to actually raise SystemExit instead of continuing
                    mock_exit.side_effect = SystemExit(1)

                    with pytest.raises(SystemExit):
                        main()

                    # Should print error and exit
                    mock_exit.assert_called_once_with(1)
                    assert any("Error:" in str(call) for call in mock_print.call_args_list)


def test_main_tool_setup():
    """Test CLI sets up correct default tools."""
    with patch("sys.argv", ["cogency", "test"]):
        with patch("cogency.Agent") as mock_agent_class:
            with patch("asyncio.run"):
                mock_agent = MagicMock()
                mock_agent_class.return_value = mock_agent

                main()

                args, kwargs = mock_agent_class.call_args
                tools = kwargs["tools"]

                # Should have base tools
                tool_names = [tool.__class__.__name__ for tool in tools]
                assert "Files" in tool_names
                assert "Shell" in tool_names
                assert "Search" in tool_names
                assert "Scrape" in tool_names
                assert "Recall" in tool_names
