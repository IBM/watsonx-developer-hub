from typing import Callable

from ibm_watsonx_ai import APIClient

from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph


from .nodes import AgentState, GraphNodes


def get_graph_closure(
    client: APIClient,
    model_id: str,
) -> Callable:
    """Graph generator closure."""

    def get_graph() -> CompiledGraph:
        """Get compiled graph with overwritten system prompt, if provided"""

        graph_nodes = GraphNodes(api_client=client, model_id=model_id)

        # Define a Graph State
        workflow = StateGraph(AgentState)

        # Add Nodes to workflow
        workflow.add_node("graph_qa", graph_nodes.graph_qa)  # agent

        workflow.add_edge(START, "graph_qa")

        workflow.add_edge("graph_qa", END)

        # Compile
        graph = workflow.compile()

        return graph

    return get_graph
