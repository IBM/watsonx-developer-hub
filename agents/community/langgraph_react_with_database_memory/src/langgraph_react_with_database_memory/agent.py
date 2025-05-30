from typing import Callable

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph_react_with_database_memory import TOOLS
from langgraph.checkpoint.postgres import PostgresSaver

def get_graph_closure(client: APIClient, model_id: str) -> Callable:
    """Graph generator closure."""

    # Initialise ChatWatsonx
    chat = ChatWatsonx(model_id=model_id, watsonx_client=client)

    # Define system prompt
    default_system_prompt = "You are a helpful AI assistant, please respond to the user's query to the best of your ability!"

    def get_graph(memory: PostgresSaver, thread_id=None, system_prompt=default_system_prompt, max_messages_in_context=10) -> CompiledGraph:
        """Get compiled graph with overwritten system prompt, if provided"""
        
        def messages_modifier(messages_from_history: list[BaseMessage]) -> list[BaseMessage]:
            """Reduces number of agent's input messages"""
            input_messages = [SystemMessage(content=system_prompt)]
            for msg in messages_from_history:
                if not isinstance(msg, SystemMessage):
                    input_messages.append(msg)

            if len(input_messages) > max_messages_in_context:
                if max_messages_in_context == 0:
                    return [] 
                elif max_messages_in_context == 1:
                    return [input_messages[0]]
                else:
                    return [input_messages[0]] + input_messages[-(max_messages_in_context - 1):]
            return input_messages
        
        if thread_id:
            return create_react_agent(chat, tools=TOOLS, checkpointer=memory, messages_modifier=messages_modifier) 
        else:
            return create_react_agent(chat, tools=TOOLS, state_modifier=system_prompt) 
            
    return get_graph