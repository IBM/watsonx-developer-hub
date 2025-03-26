from ibm_watsonx_ai import APIClient
from beeai_framework.agents.react.agent import ReActAgent
from beeai_framework.backend.chat import (
    ChatModel,
)
from beeai_framework.memory.token_memory import TokenMemory

from beeai_framework_react_agent_base import TOOLS


def get_beeai_framework_agent(client: APIClient, model_id: str, project_id: str) -> ReActAgent:
    # Initialise WatsonxChatModel
    watsonx_llm = ChatModel.from_name(
        model_id,
        {
            "project_id": project_id,
            "api_key": client.credentials.api_key,
            "api_base": client.credentials.url,
        },
    )  

    return ReActAgent(
            llm=watsonx_llm, tools=[], memory=TokenMemory(watsonx_llm)
        )
