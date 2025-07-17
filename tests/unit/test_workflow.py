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

        # Verify nodes exist - current 2-node flow
        expected_nodes = {NodeName.PRE_REACT.value, NodeName.REACT_LOOP.value, "__start__"}
        actual_nodes = set(workflow_instance.workflow.nodes.keys())
        assert actual_nodes == expected_nodes

    def test_custom_routing_table_construction(self, mock_llm, mock_tools, fs_memory_fixture):
        custom_routing_table = {
            "entry_point": NodeName.PRE_REACT.value,
            "edges": {
                NodeName.PRE_REACT.value: {"type": "direct", "destination": NodeName.REACT_LOOP.value},
                NodeName.REACT_LOOP.value: {"type": "end"}
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
        assert workflow_instance.routing_table == custom_routing_table

    @patch("cogency.workflow.partial")
    def test_dependency_injection(self, mock_partial, mock_llm, mock_tools, fs_memory_fixture, mock_response_shaper):
        Workflow(
            llm=mock_llm,
            tools=mock_tools,
            memory=fs_memory_fixture,
            response_shaper=mock_response_shaper
        )

        # Verify that partial was called for each node with correct arguments
        call_args_list = mock_partial.call_args_list

        # Check pre_react node
        pre_react_call = next((call for call in call_args_list if len(call.args) > 0 and call.args[0].__name__ == "pre_react_node"), None)
        assert pre_react_call is not None
        assert pre_react_call.kwargs["llm"] == mock_llm
        assert pre_react_call.kwargs["tools"] == mock_tools
        assert pre_react_call.kwargs["memory"] == fs_memory_fixture

        # Check react_loop node
        react_loop_call = next((call for call in call_args_list if len(call.args) > 0 and call.args[0].__name__ == "react_loop_node"), None)
        assert react_loop_call is not None
        assert react_loop_call.kwargs["llm"] == mock_llm
        assert react_loop_call.kwargs["tools"] == mock_tools
        assert react_loop_call.kwargs["response_shaper"] == mock_response_shaper