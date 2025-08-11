"""Tests for workspace functionality."""

from cogency.state import Workspace


def test_workspace_creation():
    """Test workspace creates with proper defaults."""
    ws = Workspace()

    assert ws.objective == ""
    assert ws.assessment == ""
    assert ws.approach == ""
    assert ws.observations == []
    assert ws.insights == []
    assert ws.facts == {}
    assert ws.thoughts == []


def test_workspace_with_objective():
    """Test workspace initialization with objective."""
    ws = Workspace(objective="Solve the problem")

    assert ws.objective == "Solve the problem"
    assert ws.assessment == ""
    assert ws.observations == []


def test_workspace_data_accumulation():
    """Test workspace accumulates task context."""
    ws = Workspace(objective="Research topic")

    # Add observations
    ws.observations.append("Found relevant paper")
    ws.observations.append("Expert mentioned key point")

    # Add insights
    ws.insights.append("Pattern emerges from data")

    # Add facts
    ws.facts["key_metric"] = 42
    ws.facts["source"] = "research_paper.pdf"

    # Verify accumulation
    assert len(ws.observations) == 2
    assert len(ws.insights) == 1
    assert ws.facts["key_metric"] == 42
    assert "research_paper.pdf" in ws.facts["source"]


def test_workspace_independence():
    """Test workspaces are independent instances."""
    ws1 = Workspace(objective="Task 1")
    ws2 = Workspace(objective="Task 2")

    ws1.observations.append("Observation 1")
    ws2.observations.append("Observation 2")

    assert len(ws1.observations) == 1
    assert len(ws2.observations) == 1
    assert ws1.observations[0] != ws2.observations[0]
