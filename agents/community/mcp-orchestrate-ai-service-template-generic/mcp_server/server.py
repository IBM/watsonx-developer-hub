from mcp.server.fastmcp import FastMCP
from typing import Any, Dict

from utils import (
    get_deployment_name,
    get_deployment_description,
    get_tool_name,
    get_ai_service_deployment_id,
    get_server_name,
    prepare_api_client,
    get_request_schema,
    get_response_schema,
    create_pydantic_model_from_schema,
    build_payload_from_schema,
    extract_output_from_response,
)

mcp = FastMCP(get_server_name())


def _get_dynamic_input_model():
    """
    Dynamically create the input model based on the deployment's request schema.
    Falls back to a simple model if schema is not available.
    """
    try:
        request_schema = get_request_schema()
        if request_schema:
            return create_pydantic_model_from_schema(request_schema, "ToolInputSchema")
    except Exception as e:
        print(f"Warning: Could not create dynamic model from schema: {e}")

    # Fallback to a generic model
    from pydantic import BaseModel, Field

    class FallbackInputSchema(BaseModel):
        input: str = Field(..., description="Input data for the AI service")

    return FallbackInputSchema


def _build_tool_description() -> str:
    """
    Build tool description dynamically based on deployment details and schema.
    """
    deployment_name = get_deployment_name()
    deployment_description = get_deployment_description()

    description = f"Invoke the '{deployment_name}' AI service.\n\n"

    if deployment_description:
        description += f"{deployment_description}\n\n"

    # try:
    #     request_schema = get_request_schema()
    #     if request_schema and "properties" in request_schema:
    #         description += "Input parameters:\n"
    #         for prop_name, prop_schema in request_schema["properties"].items():
    #             prop_desc = prop_schema.get("title", "") or prop_schema.get(
    #                 "description", ""
    #             )
    #             prop_type = prop_schema.get("type", "string")
    #             required = prop_name in request_schema.get("required", [])
    #             req_marker = " (required)" if required else " (optional)"
    #             description += f"- {prop_name} ({prop_type}){req_marker}: {prop_desc}\n"
    # except Exception:
    #     pass

    return description


# Create the dynamic input model
ToolInputSchema = _get_dynamic_input_model()


@mcp.tool(name=get_tool_name(), description=_build_tool_description())
def invoke_tool(input_data: ToolInputSchema) -> Dict[str, Any]:
    """
    Generic tool that invokes an AI service deployment using dynamic schema-based payload construction.
    """
    api_client = prepare_api_client()
    deployment_id = get_ai_service_deployment_id()

    # Convert Pydantic model to dict
    input_dict = input_data.model_dump()

    # Build payload based on request schema
    try:
        request_schema = get_request_schema()
        payload = (
            build_payload_from_schema(input_dict, request_schema)
            if request_schema
            else input_dict
        )
    except Exception as e:
        print(f"Warning: Could not build payload from schema, using raw input: {e}")
        payload = input_dict

    # Call the AI service
    response = api_client.deployments.run_ai_service(deployment_id, payload)

    # Extract output based on response schema
    # try:
    #     response_schema = get_response_schema()
    #     output = (
    #         extract_output_from_response(response, response_schema)
    #         if response_schema
    #         else response
    #     )
    # except Exception as e:
    #     print(f"Warning: Could not extract output from schema, using raw response: {e}")
    #     output = response

    return response


if __name__ == "__main__":
    mcp.run(transport="stdio")
