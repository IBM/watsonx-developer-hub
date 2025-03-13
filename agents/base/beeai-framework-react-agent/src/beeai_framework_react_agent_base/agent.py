from typing import Callable

from ibm_watsonx_ai import APIClient
from beeai_framework.agents.react.agent import ReActAgent
from beeai_framework.backend.chat import WatsonxChatModel
from beeai_framework.backend.message import SystemMessage
from beeai_framework.memory.unconstrained_memory import UnconstrainedMemory

from beeai_framework_react_agent_base import TOOLS


async def get_beeai_framework_agent(client: APIClient, project_id: str, model_id: str) -> Callable:
    # Initialise WatsonxChatModel
    watsonx_llm = WatsonxChatModel(
        model_id,
        settings = {
            "project_id": project_id,
            "api_key": client.credentials.api_key,
            "api_base": client.credentials.url,     
        },
     ) 

    # Define system prompt and add it to memory
    memory = UnconstrainedMemory()
    system_message = SystemMessage(content="You are a helpful AI assistant, please respond to the user's query to the best of your ability!")

    await memory.add(system_message)

    def get_agent() -> ReActAgent:

        # Create instance of ReActAgent
        return ReActAgent(
            llm=watsonx_llm, tools=TOOLS, memory=UnconstrainedMemory()
        )

    return get_agent
