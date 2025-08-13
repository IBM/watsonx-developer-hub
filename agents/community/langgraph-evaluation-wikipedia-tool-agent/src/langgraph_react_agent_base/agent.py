from typing import Callable

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper



def get_graph_closure(client: APIClient, model_id: str) -> Callable:
    """Graph generator closure."""
    TOOLS = [WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())]
    # Initialise ChatWatsonx
    chat = ChatWatsonx(model_id=model_id, watsonx_client=client, params={"temperature": 0.01})

    # Define system prompt
    default_system_prompt = "You are a helpful AI assistant, please respond to the user's query to the best of your ability!"

    def get_graph(system_prompt=default_system_prompt) -> CompiledGraph:
        """Get compiled graph with overwritten system prompt, if provided"""
        
        # Create instance of compiled graph
        return create_react_agent(
            chat, tools=TOOLS, state_modifier=system_prompt
        )

    return get_graph
