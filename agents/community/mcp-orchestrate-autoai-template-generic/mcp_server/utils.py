import os
from typing import Any

from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from pydantic import BaseModel, Field, create_model

from generated_config import INPUT_FIELDS, PREDICTION_COLUMN, SERVER_NAME, TOOL_NAME


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


def get_autoai_deployment_id() -> str:
    load_env()
    deployment_id = os.getenv("WATSONX_AUTOAI_DEPLOYMENT_ID")
    if not deployment_id:
        raise ValueError("WATSONX_AUTOAI_DEPLOYMENT_ID is not set")
    return deployment_id


def get_server_name() -> str:
    return SERVER_NAME


def get_tool_name() -> str:
    return TOOL_NAME


def get_input_fields() -> list[dict[str, Any]]:
    return INPUT_FIELDS


def python_type_for_field(field: dict[str, Any]) -> type:
    field_type = str(field.get("type", "string")).lower()
    if field_type in {"integer", "int64", "int32"}:
        return int
    if field_type in {"number", "float", "double", "decimal"}:
        return float
    if field_type in {"boolean", "bool"}:
        return bool
    return str


def create_input_model() -> type[BaseModel]:
    model_fields: dict[str, tuple[type, Field]] = {}

    for field in get_input_fields():
        field_name = field["name"]
        description = field.get("description") or f"Input value for {field_name}"
        model_fields[field_name] = (
            python_type_for_field(field),
            Field(..., description=description),
        )

    return create_model("AutoAIInput", **model_fields)


def build_scoring_payload(input_model: BaseModel) -> dict[str, Any]:
    fields = [field["name"] for field in get_input_fields()]
    values = [getattr(input_model, field_name) for field_name in fields]

    return {
        "input_data": [
            {
                "fields": fields,
                "values": [values],
            }
        ]
    }


def extract_prediction(response: dict[str, Any]) -> Any:
    try:
        predictions = response["predictions"][0]
        values = predictions["values"][0]
        if len(values) == 1:
            return values[0]
        return values
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            f"Unexpected response structure from deployment: {response}"
        ) from error


def get_prediction_column() -> str:
    return PREDICTION_COLUMN
