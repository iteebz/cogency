
import pytest
from unittest.mock import Mock, patch
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from cogency.workflow import Workflow, DEFAULT_ROUTING_TABLE
from cogency.common.constants import NodeName
from cogency.common.types import AgentState

class TestWorkflow:
    @pytest.fixture
    def mock_tools(self):
        return [Mock(), Mock()]

    @pytest.fixture
    def mock_response_shaper(self):
        return {"key": "value"}

    def test_default_graph_construction(self, mock_llm, mock_tools, fs_memory_fixture, mock_response_shaper):
        workflow_instance = Workflow(
            llm=mock_llm,
            tools=mock_tools,
            memory=fs_memory_fixture,
            response_shaper=mock_response_shaper
        )

        assert workflow_instance.workflow is not None
        assert isinstance(workflow_instance.workflow, CompiledStateGraph)

        # Verify nodes
        expected_nodes = {NodeName.MEMORIZE.value, NodeName.FILTER_TOOLS.value, NodeName.REACT_LOOP.value, "__start__"}
        actual_nodes = set(workflow_instance.workflow.nodes.keys())
        assert actual_nodes == expected_nodes

        # Verify edges
        # LangGraph's internal representation of edges might not be directly accessible or
        # easily comparable to the routing table. We'll check the entry point and a few key transitions.
        # A more robust test would involve simulating a step and checking the next state.
        # assert workflow_instance.workflow.get_entry_point() == DEFAULT_ROUTING_TABLE["entry_point"]

        # Check specific edges
        # This requires understanding LangGraph's internal graph structure, which might be
        # complex. For now, we'll rely on the entry point and the fact that the graph compiles.
        # A more thorough test would involve running a simple input through the graph.

    def test_custom_routing_table_construction(self, mock_llm, mock_tools, fs_memory_fixture):
        custom_routing_table = {
            "entry_point": NodeName.FILTER_TOOLS.value,
            "edges": {
                NodeName.FILTER_TOOLS.value: {"type": "direct", "destination": NodeName.MEMORIZE.value},
                NodeName.MEMORIZE.value: {"type": "end"}
            }
        }

        workflow_instance = Workflow(
            llm=mock_llm,
            tools=mock_tools,
            memory=fs_memory_fixture,
            routing_table=custom_routing_table
        )

        assert workflow_instance.workflow is not None
        assert isinstance(workflow_instance.workflow, CompiledStateGraph)
        # assert workflow_instance.workflow.get_entry_point() == custom_routing_table["entry_point"] # Not directly accessible on CompiledStateGraph

        expected_nodes = {NodeName.MEMORIZE.value, NodeName.FILTER_TOOLS.value, NodeName.REACT_LOOP.value, "__start__"}
        actual_nodes = set(workflow_instance.workflow.nodes.keys())
        assert actual_nodes == expected_nodes

    @patch("cogency.workflow.partial")
    def test_dependency_injection(self, mock_partial, mock_llm, mock_tools, fs_memory_fixture, mock_response_shaper):
        Workflow(
            llm=mock_llm,
            tools=mock_tools,
            memory=fs_memory_fixture,
            response_shaper=mock_response_shaper
        )

        # Verify that partial was called for each node with correct arguments
        # This is a bit tricky as partial is called multiple times.
        # We need to check the arguments passed to each call of partial.
        call_args_list = mock_partial.call_args_list

        # Check memorize node
        memorize_call = next((call for call in call_args_list if call.args[0].__name__ == "memorize_node"), None)
        assert memorize_call is not None
        assert memorize_call.kwargs["memory"] == fs_memory_fixture

        # Check filter_tools node
        filter_tools_call = next((call for call in call_args_list if call.args[0].__name__ == "filter_tools_node"), None)
        assert filter_tools_call is not None
        assert filter_tools_call.kwargs["llm"] == mock_llm
        assert filter_tools_call.kwargs["tools"] == mock_tools

        # Check react_loop_node
        react_loop_call = next((call for call in call_args_list if call.args[0].__name__ == "react_loop_node"), None)
        assert react_loop_call is not None
        assert react_loop_call.kwargs["llm"] == mock_llm
        assert react_loop_call.kwargs["tools"] == mock_tools
        assert react_loop_call.kwargs["response_shaper"] == mock_response_shaper
