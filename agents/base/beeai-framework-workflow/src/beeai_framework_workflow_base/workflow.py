from beeai_framework.backend.chat import (
    ChatModel,
)
from beeai_framework.workflows.agent import AgentWorkflow
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.weather.openmeteo import OpenMeteoTool

def get_beeai_framework_workflow(token: str, url: str, model_id: str, project_id: str) -> AgentWorkflow:
    # Initialise WatsonxChatModel
    watsonx_llm = ChatModel.from_name(
        "watsonx:" + model_id,
        {
            "project_id": project_id,
            "token": token,
            "api_base": url,
        },
    )  
    workflow = AgentWorkflow("Travel Advisor")

    workflow.add_agent(
        name="Weather Forecaster",
        role="A diligent weather forecaster",
        instructions="You specialize in reporting on the weather.",
        tools=[OpenMeteoTool()],
        llm=watsonx_llm,
    )

    workflow.add_agent(
        name="Acivity Planner",
        role="An expert in local attractions",
        instructions="You know about interesting activities and would like to share.",
        tools=[DuckDuckGoSearchTool()],
        llm=watsonx_llm,
    )

    workflow.add_agent(
        name="Travel Advisor",
        role="A travel advisor",
        instructions="You can synthesize travel details such as weather and recommended activities and provide a coherent summary.",
        llm=watsonx_llm,
    )

    return workflow
