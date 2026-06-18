from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from utils import (
    get_deployment_name,
    get_deployment_description,
    get_rag_answer_tool_name,
    get_rag_deployment_id,
    get_rag_deployment_details_tool_name,
    get_required_env_status,
    get_server_name,
    prepare_api_client,
)

mcp = FastMCP(get_server_name())


class RAGQuestionInput(BaseModel):
    question: str = Field(
        ..., description="The question to ask the RAG Pattern AI service"
    )


def _build_tool_description() -> str:
    deployment_name = get_deployment_name()

    return (
        f"Ask a question to the '{deployment_name}' RAG Pattern AI service.\n\n"
        "Provide a question as a string, and the AI service will return an answer "
        "based on its knowledge base.\n\n"
        "Returns the answer from the RAG Pattern deployment."
    )


@mcp.tool(name=get_rag_answer_tool_name(), description=_build_tool_description())
def invoke_rag_question(input_data: RAGQuestionInput):
    api_client = prepare_api_client()
    deployment_id = get_rag_deployment_id()

    payload = {"messages": [{"role": "user", "content": input_data.question}]}

    score_response = api_client.deployments.run_ai_service(deployment_id, payload)

    output_for_user = score_response["choices"][0]["message"]["content"]

    return {
        "question": input_data.question,
        "answer": output_for_user,
        "deployment_name": get_deployment_name(),
        "deployment_id": deployment_id,
    }


@mcp.tool(
    name=get_rag_deployment_details_tool_name(),
    description="Return configuration-oriented details about the watsonx.ai AutoAI RAG deployment used by this toolkit.",
)
def get_rag_pattern_deployment_details():
    deployment_id = get_rag_deployment_id()

    return {
        "deployment_name": get_deployment_name(),
        "deployment_description": get_deployment_description(),
        "deployment_id": deployment_id,
        "server_name": get_server_name(),
        "required_environment_variables": get_required_env_status(),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
