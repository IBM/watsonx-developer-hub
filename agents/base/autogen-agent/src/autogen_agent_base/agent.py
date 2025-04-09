from typing import Callable

from ibm_watsonx_ai import Credentials

from autogen_watsonx_client.config import WatsonxClientConfiguration
from autogen_watsonx_client.client import WatsonXChatCompletionClient

from autogen_agentchat.agents import AssistantAgent

from autogen_agent_base import TOOLS


def get_agent_chat(
    credentials: Credentials,
    model_id: str,
    space_id: str | None = None,
) -> Callable:
    """Workflow generator closure."""

    # Initialise WatsonxClientConfiguration
    wx_config = WatsonxClientConfiguration(
        model_id=model_id,  # pick a model you have access to on wx.ai here
        token=credentials.token,
        url=credentials.url,
        space_id=space_id,
    )

    wx_client = WatsonXChatCompletionClient(**wx_config)

    # Define system prompt
    default_system_prompt = "You are a helpful AI assistant, please respond to the user's query to the best of your ability!"

    def get_agent(system_prompt: str = default_system_prompt) -> AssistantAgent:
        """Get compiled workflow with overwritten system prompt, if provided"""

        # Create instance of compiled workflow
        return AssistantAgent(
            name="assistant",
            model_client=wx_client,
            tools=TOOLS,
            system_message=system_prompt,
            model_client_stream=True,
            reflect_on_tool_use=True,
        )

    return get_agent
