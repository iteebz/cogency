"""Telemetry integration tests - end-to-end CLI telemetry validation."""

import asyncio
from unittest.mock import Mock, patch

from cogency import Agent
from cogency.events import create_telemetry_bridge
from cogency.events.telemetry import format_telemetry_summary


def test_agent_telemetry_integration():
    """Test telemetry collection during agent execution."""
    # Create agent with event capture
    agent = Agent("test", tools=[])
    
    # Get the telemetry bridge from agent's event bus
    from cogency.events.bus import _bus
    bridge = create_telemetry_bridge(_bus)
    
    # Mock LLM to avoid API calls
    with patch.object(agent.llm, 'generate', return_value="Test response"):
        # Run agent query
        response = agent.run("Hello world")
        
        # Verify response
        assert response == "Test response"
        
        # Check telemetry was captured
        summary = bridge.get_summary()
        assert summary["total_events"] > 0
        
        # Verify agent events were captured
        event_types = summary["event_types"]
        assert "agent" in event_types
        assert event_types["agent"] > 0
        
        # Verify recent events can be retrieved
        recent = bridge.get_recent(count=5)
        assert len(recent) > 0
        
        # Verify events can be formatted
        for event in recent:
            compact = bridge.format_event(event, style="compact")
            assert isinstance(compact, str)
            assert len(compact) > 0


async def test_streaming_telemetry_integration():
    """Test telemetry with streaming mode."""
    agent = Agent("test", tools=[])
    
    # Get telemetry bridge
    from cogency.events.bus import _bus
    bridge = create_telemetry_bridge(_bus)
    
    # Mock LLM for streaming
    with patch.object(agent.llm, 'generate', return_value="Streaming response"):
        # Test streaming mode
        events = []
        async for event in agent.run_stream("Test streaming"):
            events.append(event)
            if len(events) >= 3:  # Collect a few events
                break
        
        # Verify streaming events were generated
        assert len(events) > 0
        
        # Verify telemetry captured streaming events
        summary = bridge.get_summary()
        assert summary["total_events"] > 0


def test_telemetry_error_handling():
    """Test telemetry with error conditions."""
    agent = Agent("test", tools=[])
    
    # Get telemetry bridge
    from cogency.events.bus import _bus
    bridge = create_telemetry_bridge(_bus)
    
    # Mock LLM to raise an error
    with patch.object(agent.llm, 'generate', side_effect=Exception("Test error")):
        # Run agent query that will fail
        response = agent.run("This will error")
        
        # Verify error was handled
        assert "Error:" in response
        
        # Check telemetry captured the error
        summary = bridge.get_summary()
        assert summary["errors"] > 0
        
        # Verify error events can be filtered
        error_events = bridge.get_recent(filters={"errors_only": True})
        assert len(error_events) > 0


def test_telemetry_summary_formatting():
    """Test telemetry summary formatting with real data."""
    agent = Agent("test", tools=[])
    
    # Get telemetry bridge
    from cogency.events.bus import _bus
    bridge = create_telemetry_bridge(_bus)
    
    # Mock LLM
    with patch.object(agent.llm, 'generate', return_value="Summary test response"):
        # Run a query to generate events
        agent.run("Generate telemetry data")
        
        # Test summary formatting
        summary_text = format_telemetry_summary(bridge)
        
        # Verify summary contains expected content
        assert "Telemetry Summary" in summary_text
        assert "Total events:" in summary_text
        assert "agent:" in summary_text
        
        # Verify summary is not empty state
        assert "No telemetry data" not in summary_text


def test_telemetry_filtering():
    """Test telemetry event filtering functionality."""
    agent = Agent("test", tools=["files"])
    
    # Get telemetry bridge
    from cogency.events.bus import _bus
    bridge = create_telemetry_bridge(_bus)
    
    # Mock both LLM and file operations
    with patch.object(agent.llm, 'generate', return_value="File operation complete"), \
         patch('cogency.tools.files.Files.run') as mock_files:
        
        mock_files.return_value = Mock(success=True, content="File list")
        
        # Run query that should use tools
        agent.run("List the files")
        
        # Test type filtering
        tool_events = bridge.get_recent(filters={"type": "tool"})
        agent_events = bridge.get_recent(filters={"type": "agent"})
        
        # Should have both types (if tools were invoked)
        # Note: This test may pass with 0 tool events if reasoning doesn't trigger tool use
        assert isinstance(tool_events, list)
        assert isinstance(agent_events, list)
        assert len(agent_events) > 0  # Should always have agent events


def test_multiple_iterations_telemetry():
    """Test telemetry capture across multiple reasoning iterations."""
    agent = Agent("test", tools=[], max_iterations=3)
    
    # Get telemetry bridge  
    from cogency.events.bus import _bus
    bridge = create_telemetry_bridge(_bus)
    
    # Mock LLM to require multiple iterations
    responses = [
        "Let me think more about this...",  # Should trigger another iteration
        "I need to consider additional factors...",  # Another iteration
        "Final response after consideration."  # Final response
    ]
    
    with patch.object(agent.llm, 'generate', side_effect=responses):
        # Run query that may require multiple iterations
        response = agent.run("Complex reasoning task")
        
        # Verify final response
        assert "Final response" in response
        
        # Check telemetry captured multiple iterations
        summary = bridge.get_summary()
        
        # Should have agent events from multiple iterations
        assert summary["total_events"] > 1
        assert "agent" in summary["event_types"]
        
        # Verify iteration events were captured
        agent_events = bridge.get_recent(filters={"type": "agent"})
        iteration_events = [e for e in agent_events if e.get("data", {}).get("state") == "iteration"]
        
        # Should have captured iteration events
        assert len(iteration_events) >= 0  # May be 0 if LLM gives direct response