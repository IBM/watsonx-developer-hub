from typing import Callable

from ibm_watsonx_ai import APIClient

from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph


from .nodes import AgentState, GraphNodes


def get_graph_closure(
    client: APIClient,
    model_id: str,
    embedding_model_id: str
) -> Callable:
    """Graph generator closure."""

    def get_graph() -> CompiledGraph:
        """Get compiled graph with overwritten system prompt, if provided"""

        graph_nodes = GraphNodes(api_client=client, model_id=model_id, embedding_model_id=embedding_model_id)

        # Define a Graph State
        workflow = StateGraph(AgentState)

        # Add Nodes to workflow
        workflow.add_node("retriever", graph_nodes.retriever)  # agent
        workflow.add_node("generate", graph_nodes.generate)  # agent

        workflow.add_edge(START, "retriever")
        workflow.add_edge("retriever", "generate")

        workflow.add_edge("generate", END)

        # Compile
        graph = workflow.compile()

        return graph

    return get_graph
