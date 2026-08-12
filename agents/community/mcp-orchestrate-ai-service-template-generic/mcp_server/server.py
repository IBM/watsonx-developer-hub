from mcp.server.fastmcp import FastMCP
from typing import Any, Dict
from functools import lru_cache
import sys
import logging

from utils import (
    get_tool_name,
    get_ai_service_deployment_ids,
    get_server_name,
    prepare_api_client,
    get_request_schema,
    create_pydantic_model_from_schema,
    build_payload_from_schema,
    get_deployment_details,
    load_env,
)

# Configure logging to stderr to avoid breaking JSONRPC protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(get_server_name())

# Flag to track if tools have been registered
_tools_registered = False


@lru_cache(maxsize=128)
def _get_dynamic_input_model(deployment_id: str):
    """
    Dynamically create the input model based on the deployment's request schema.
    Falls back to a simple model if schema is not available.

    Args:
        deployment_id: The deployment ID to create model for
    """
    try:
        request_schema = get_request_schema(deployment_id)
        if request_schema:
            return create_pydantic_model_from_schema(
                request_schema, f"ToolInputSchema_{deployment_id.replace('-', '_')}"
            )
    except Exception as e:
        logger.warning(
            f"Could not create dynamic model from schema for {deployment_id}: {e}"
        )

    # Fallback to a generic model
    from pydantic import BaseModel, Field

    class FallbackInputSchema(BaseModel):
        input: str = Field(..., description="Input data for the AI service")

    return FallbackInputSchema


def _build_tool_description(deployment_id: str, deployment_index: str) -> str:
    """
    Build tool description dynamically based on deployment details and schema.

    Args:
        deployment_id: The deployment ID
        deployment_index: The index/identifier for this deployment
    """
    api_client = prepare_api_client()

    try:
        deployment_details = get_deployment_details(api_client, deployment_id)
        deployment_name = deployment_details.get("metadata", {}).get(
            "name", f"Deployment {deployment_index}"
        )
        deployment_description = deployment_details.get("metadata", {}).get(
            "description", ""
        )

        description = f"Invoke the '{deployment_name}' AI service (Deployment {deployment_index}).\n\n"

        if deployment_description:
            description += f"{deployment_description}\n\n"

        description += f"Deployment ID: {deployment_id}"

        return description
    except Exception as e:
        logger.warning(f"Could not fetch deployment details for {deployment_id}: {e}")
        return f"Invoke AI service deployment {deployment_index}.\n\nDeployment ID: {deployment_id}"


def _create_tool_function(deployment_id: str, deployment_index: str):
    """
    Create a tool function for a specific deployment.

    Args:
        deployment_id: The deployment ID
        deployment_index: The index/identifier for this deployment
    """
    # Get the dynamic input model for this deployment
    ToolInputSchema = _get_dynamic_input_model(deployment_id)

    def invoke_tool(input_data: ToolInputSchema) -> Dict[str, Any]:
        """
        Tool that invokes an AI service deployment using dynamic schema-based payload construction.
        """
        api_client = prepare_api_client()

        # Convert Pydantic model to dict
        input_dict = input_data.model_dump()

        # Build payload based on request schema
        try:
            request_schema = get_request_schema(deployment_id)
            payload = (
                build_payload_from_schema(input_dict, request_schema)
                if request_schema
                else input_dict
            )
        except Exception as e:
            logger.warning(f"Could not build payload from schema, using raw input: {e}")
            payload = input_dict

        # Call the AI service
        response = api_client.deployments.run_ai_service(deployment_id, payload)

        return response

    return invoke_tool


def validate_environment():
    """
    Validate that all required environment variables are set.
    Raises ValueError if validation fails.
    """
    # Load environment variables
    load_env()

    # Try to get deployment IDs to validate environment
    try:
        deployment_ids = get_ai_service_deployment_ids()
        logger.info(
            f"Environment validation successful: Found {len(deployment_ids)} deployment ID(s)"
        )
        return deployment_ids
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise


def register_tools():
    """
    Register a separate tool for each deployment ID found in environment variables.
    This function is called lazily to ensure environment is loaded first.
    """
    global _tools_registered

    if _tools_registered:
        logger.info("Tools already registered, skipping")
        return

    try:
        # Validate environment and get deployment IDs
        deployment_ids = validate_environment()

        logger.info(f"Registering tools for {len(deployment_ids)} deployment(s)")

        for index, deployment_id in deployment_ids.items():
            # Create tool name based on index
            if index == "default":
                tool_name = get_tool_name()
            else:
                tool_name = f"{get_tool_name()}_{index}"

            # Build description
            description = _build_tool_description(deployment_id, index)

            # Create and register the tool
            tool_func = _create_tool_function(deployment_id, index)

            # Register with MCP
            mcp.tool(name=tool_name, description=description)(tool_func)

            logger.info(f"Registered tool: {tool_name} for deployment {deployment_id}")

        _tools_registered = True
        logger.info("Tool registration complete")

    except Exception as e:
        logger.error(f"Error registering tools: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        # Register tools before starting the server
        register_tools()

        # Start the MCP server
        logger.info("Starting MCP server")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)
