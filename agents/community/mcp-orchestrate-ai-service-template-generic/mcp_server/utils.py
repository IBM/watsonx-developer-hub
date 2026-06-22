import os
from typing import Dict, Any, Optional, Type
from functools import lru_cache

from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from pydantic import BaseModel, Field, create_model

from generated_config import (
    DEPLOYMENT_NAME,
    DEPLOYMENT_DESCRIPTION,
    SERVER_NAME,
    TOOL_NAME,
)


def load_env() -> None:
    load_dotenv()


def prepare_api_client() -> APIClient:
    load_env()
    return APIClient(
        credentials=Credentials(
            url=os.getenv("WATSONX_URL"),
            api_key=os.getenv("WATSONX_API_KEY"),
        ),
        space_id=os.getenv("WATSONX_SPACE_ID"),
    )


def get_ai_service_deployment_id() -> str:
    load_env()
    deployment_id = os.getenv("WATSONX_AI_SERVICE_DEPLOYMENT_ID")
    if not deployment_id:
        raise ValueError("WATSONX_AI_SERVICE_DEPLOYMENT_ID is not set")
    return deployment_id


def get_server_name() -> str:
    return SERVER_NAME


def get_tool_name() -> str:
    return TOOL_NAME


def get_deployment_name() -> str:
    return DEPLOYMENT_NAME


def get_deployment_description() -> str:
    return DEPLOYMENT_DESCRIPTION


def get_required_env_status() -> dict:
    load_env()
    required_env_vars = [
        "WATSONX_URL",
        "WATSONX_API_KEY",
        "WATSONX_SPACE_ID",
        "WATSONX_AI_SERVICE_DEPLOYMENT_ID",
    ]

    return {env_var: bool(os.getenv(env_var)) for env_var in required_env_vars}


def get_deployment_details(api_client: APIClient) -> Dict[str, Any]:
    """
    Fetch deployment details.
    """
    deployment_id = get_ai_service_deployment_id()

    try:
        details = api_client.deployments.get_details(deployment_id)
        return details
    except Exception as e:
        raise RuntimeError(f"Failed to fetch deployment details: {e}")


@lru_cache(maxsize=1)
def get_ai_service_details() -> Dict[str, Any]:
    """
    Fetch AI service details including documentation schema.
    Cached to avoid repeated API calls.
    """
    api_client = prepare_api_client()
    deployment_details = get_deployment_details(api_client)
    ai_service_id = deployment_details["entity"]["asset"]["id"]

    return api_client.repository.get_ai_service_details(ai_service_id)


def get_request_schema() -> Optional[Dict[str, Any]]:
    """
    Extract request schema from deployment documentation.
    Returns the JSON schema for the request payload.
    """
    details = get_ai_service_details()

    try:
        documentation = details.get("entity", {}).get("documentation", {})
        request_schema = documentation.get("request", {}).get("application/json", {})
        return request_schema if request_schema else None
    except (KeyError, AttributeError):
        return None


def get_response_schema() -> Optional[Dict[str, Any]]:
    """
    Extract response schema from deployment documentation.
    Returns the JSON schema for the response payload.
    """
    details = get_ai_service_details()

    try:
        documentation = details.get("entity", {}).get("documentation", {})
        response_schema = documentation.get("response", {}).get("application/json", {})
        return response_schema if response_schema else None
    except (KeyError, AttributeError):
        return None


def build_payload_from_schema(
        input_data: Dict[str, Any], schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build API payload from input data based on the request schema.

    Args:
        input_data: Dictionary containing user input
        schema: JSON schema defining the expected structure

    Returns:
        Properly structured payload for the API call
    """
    if not schema or "properties" not in schema:
        return input_data

    payload = {}
    properties = schema.get("properties", {})

    for prop_name, prop_schema in properties.items():
        if prop_name in input_data:
            payload[prop_name] = input_data[prop_name]

    return payload


def extract_output_from_response(
        response: Dict[str, Any], schema: Dict[str, Any]
) -> Any:
    """
    Extract relevant output from API response based on the response schema.

    Args:
        response: Raw API response
        schema: JSON schema defining the response structure

    Returns:
        Extracted output value(s)
    """
    if not schema or "properties" not in schema:
        return response

    properties = schema.get("properties", {})

    # Try to extract the main content based on common patterns
    # For chat-like responses, look for choices[0].message.content
    if "choices" in properties and "choices" in response:
        choices = response.get("choices", [])
        if choices and len(choices) > 0:
            message = choices[0].get("message", {})
            if "content" in message:
                return message["content"]
            # Handle streaming delta format
            if "delta" in message:
                delta = message.get("delta", {})
                if "content" in delta:
                    return delta["content"]

    # For simpler responses, return the first property value
    for prop_name in properties.keys():
        if prop_name in response:
            return response[prop_name]

    # Fallback to returning the entire response
    return response


def create_pydantic_model_from_schema(
        schema: Dict[str, Any], model_name: str = "DynamicModel"
) -> Type[BaseModel]:
    """
    Create a Pydantic model dynamically from a JSON schema.

    Args:
        schema: JSON schema dictionary
        model_name: Name for the generated model

    Returns:
        Dynamically created Pydantic model class
    """
    if not schema or "properties" not in schema:
        # Return a simple model with a generic field
        return create_model(
            model_name, input=(str, Field(..., description="Generic input"))
        )

    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))
    field_definitions = {}

    for prop_name, prop_schema in properties.items():
        field_type = _json_schema_type_to_python(prop_schema)
        field_description = prop_schema.get("title", "") or prop_schema.get(
            "description", ""
        )
        is_required = prop_name in required_fields

        field_definitions[prop_name] = (
            field_type,
            Field(... if is_required else None, description=field_description),
        )

    return create_model(model_name, **field_definitions)


def _json_schema_type_to_python(prop_schema: Dict[str, Any]) -> type:
    """
    Convert JSON schema type to Python type for Pydantic.

    Args:
        prop_schema: Property schema dictionary

    Returns:
        Python type
    """
    schema_type = prop_schema.get("type", "string")

    # Handle array types
    if schema_type == "array":
        items_schema = prop_schema.get("items", {})
        item_type = _json_schema_type_to_python(items_schema)
        return list[item_type]

    # Handle basic types
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "object": dict,
        "null": type(None),
    }

    return type_mapping.get(schema_type, str)
