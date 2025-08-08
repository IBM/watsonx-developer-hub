from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.backend.chat import (
    ChatModel,
)
from beeai_framework.agents.experimental.requirements.conditional import ConditionalRequirement
from beeai_framework.memory.token_memory import TokenMemory
from beeai_framework.tools import Tool
from beeai_framework.tools.think import ThinkTool

from beeai_framework_requirement_agent_base import TOOLS


def get_beeai_framework_agent(token: str, url: str, model_id: str, project_id: str) -> RequirementAgent:
    # Initialise WatsonxChatModel
    watsonx_llm = ChatModel.from_name(
        "watsonx:" + model_id,
        {
            "project_id": project_id,
            "token": token,
            "api_base": url,
        },
    )  

    return RequirementAgent(
            llm=watsonx_llm, tools=TOOLS, memory=TokenMemory(watsonx_llm), requirements=[ConditionalRequirement(ThinkTool, force_at_step=1, force_after=Tool, consecutive_allowed=False)],
        )
