from mcp.server.fastmcp import FastMCP

from utils import (
    get_deployment_name,
    get_rag_deployment_id,
    get_server_name,
    get_tool_name,
    prepare_api_client,
)

mcp = FastMCP(get_server_name())


def _build_tool_description() -> str:
    deployment_name = get_deployment_name()

    return (
        f"Ask a question to the '{deployment_name}' RAG Pattern AI service.\n\n"
        "Provide a question as a string, and the AI service will return an answer "
        "based on its knowledge base.\n\n"
        "Returns the answer from the RAG Pattern deployment."
    )


@mcp.tool(name=get_tool_name(), description=_build_tool_description())
def ask_rag_question(question: str):
    """
    Ask a question to the AutoAI RAG Pattern AI service.

    Args:
        question: The question to ask the RAG Pattern AI service

    Returns:
        dict: Contains the answer from the AI service
    """
    api_client = prepare_api_client()
    deployment_id = get_rag_deployment_id()

    payload = {"messages": [{"role": "user", "content": question}]}

    score_response = api_client.deployments.run_ai_service(deployment_id, payload)

    output_for_user = score_response["choices"][0]["message"]["content"]

    return {
        "question": question,
        "answer": output_for_user,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")

# Made with Bob
