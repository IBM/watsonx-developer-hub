from mcp.server.fastmcp import FastMCP

from utils import (
    build_scoring_payload,
    create_input_model,
    extract_prediction,
    get_autoai_deployment_id,
    get_prediction_column,
    get_server_name,
    get_tool_name,
    prepare_api_client,
)

mcp = FastMCP(get_server_name())
AutoAIInput = create_input_model()


def _build_tool_description() -> str:
    prediction_column = get_prediction_column()

    return (
        f"Predict the value of '{prediction_column}' using the deployed watsonx.ai AutoAI model.\n\n"
        "Provide all required input fields defined by the generated schema.\n\n"
        "Returns the prediction result from the deployment."
    )


@mcp.tool(name=get_tool_name(), description=_build_tool_description())
def invoke_autoai_prediction(input_data: AutoAIInput):
    api_client = prepare_api_client()
    deployment_id = get_autoai_deployment_id()
    prediction_column = get_prediction_column()

    payload = build_scoring_payload(input_data)
    response = api_client.deployments.score(deployment_id, meta_props=payload)
    return {
        "prediction_column": prediction_column,
        "prediction": extract_prediction(response),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
