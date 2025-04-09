from typing import Callable

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from langgraph_tavily_tool import tavily_search_watsonx


def get_graph_closure(
    client: APIClient, model_id: str, service_manager_service_url: str, secret_id: str
) -> Callable:
    """Graph generator closure."""

    # Initialise ChatWatsonx
    chat = ChatWatsonx(model_id=model_id, watsonx_client=client)

    TOOLS = [
        tavily_search_watsonx(
            api_client=client,
            service_manager_service_url=service_manager_service_url,
            secret_id=secret_id,
        )
    ]

    # Define system prompt
    default_system_prompt = "You are a helpful AI assistant, please respond to the user's query to the best of your ability!"

    # Initialise memory saver
    memory = MemorySaver()

    def get_graph(system_prompt=default_system_prompt) -> CompiledGraph:
        """Get compiled graph with overwritten system prompt, if provided"""

        # Create instance of compiled graph
        return create_react_agent(
            chat,
            tools=TOOLS,
            checkpointer=memory,
            state_modifier=system_prompt,
        )

    return get_graph
