from typing import Callable

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from langgraph_react_agent_base import retriever_tool_watsonx


def get_graph_closure(client: APIClient, model_id: str, tool_config: dict) -> Callable:
    """Graph generator closure."""

    # Initialise ChatWatsonx
    chat = ChatWatsonx(model_id=model_id, watsonx_client=client)

    TOOLS = [retriever_tool_watsonx(api_client=client, tool_config=tool_config)]

    # Define system prompt
    default_system_prompt = "You are a helpful AI assistant, please respond to the user's query to the best of your ability!"

    # Initialise memory saver
    memory = MemorySaver()

    def get_graph(system_prompt=default_system_prompt) -> CompiledGraph:
        """Get compiled graph with overwritten system prompt, if provided"""

        # Create instance of compiled graph
        return create_react_agent(
            chat, tools=TOOLS, checkpointer=memory, state_modifier=system_prompt
        )

    return get_graph
