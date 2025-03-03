from typing import Callable

from ibm_watsonx_ai import APIClient
from llama_index.llms.ibm import WatsonxLLM

from llama_index_workflow_agent_base import TOOLS
from llama_index_workflow_agent_base.workflow import FunctionCallingAgent


def get_workflow_closure(client: APIClient, model_id: str) -> Callable:
    """Workflow generator closure."""

    # Initialise WatsonxLLM
    chat = WatsonxLLM(model_id=model_id, api_client=client)

    # Define system prompt
    default_system_prompt = "You are a helpful AI assistant, please respond to the user's query to the best of your ability!"

    def get_agent(system_prompt: str = default_system_prompt) -> FunctionCallingAgent:
        """Get compiled workflow with overwritten system prompt, if provided"""

        # Create instance of compiled workflow
        return FunctionCallingAgent(
            llm=chat,
            tools=TOOLS,
            system_prompt=system_prompt,
            timeout=120,
            verbose=False,
        )

    return get_agent
