from typing import Callable
from functools import partial

from ibm_watsonx_ai import APIClient

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph


from .nodes import AgentState, GraphNodes


def get_graph_closure(
    client: APIClient,
    model_id: str,
    embedding_model_id: str,
    knowledge_graph_description: str,
    service_manager_service_url: str,
    secret_id: str,
) -> Callable:
    """Graph generator closure."""

    def get_graph(system_message: SystemMessage | None = None) -> CompiledStateGraph:
        """Get compiled graph with overwritten system prompt, if provided"""

        if system_message is None:
            system_message = SystemMessage(
                content=(
                    "You are a helpful AI assistant, please respond to the user's query to the best of your ability! "
                    "If relevant, please use knowledge from the provided documents."
                )
            )
        graph_nodes = GraphNodes(
            api_client=client,
            model_id=model_id,
            embedding_model_id=embedding_model_id,
            system_message=system_message,
            service_manager_service_url=service_manager_service_url,
            secret_id=secret_id,
        )

        # Define a Graph State
        workflow = StateGraph(AgentState)

        # Add Nodes to workflow

        # Routing
        workflow.add_node(
            "agent",
            partial(
                graph_nodes.agent,
                knowledge_graph_description=knowledge_graph_description,
            ),
        )

        # Graph Search
        workflow.add_node("graph_search", graph_nodes.graph_search)

        # Vector Index Retriever
        workflow.add_node("vector_retriever", graph_nodes.unstructured_retriever)

        # Generate final answer
        workflow.add_node("generate", graph_nodes.generate)

        workflow.add_edge(START, "agent")

        # Set up edges
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            lambda state: state["route"],
            {
                "graph_knowledge_base": "graph_search",  # If graph knowledge base is in state
                # Otherwise we finish.
                "final_answer": "generate",
            },
        )
        workflow.add_edge("graph_search", "vector_retriever")
        workflow.add_edge("vector_retriever", "generate")

        workflow.add_edge("generate", END)

        # Compile
        graph = workflow.compile()

        return graph

    return get_graph
