import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from pydantic import BaseModel, Field, create_model

# Loaded once at module import — in Orchestrate runtime the variables come
# from toolkit.yaml `env:` anyway, and load_dotenv() is a no-op when .env is absent.
load_dotenv()

SERVER_NAME = "autoai-generic-toolkit"
TOOL_NAME = "get_autoai_prediction"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not set")
    return value


def prepare_api_client() -> APIClient:
    return APIClient(
        credentials=Credentials(
            url=require_env("WATSONX_URL"),
            api_key=require_env("WATSONX_API_KEY"),
        ),
        space_id=require_env("WATSONX_SPACE_ID"),
    )


def get_autoai_deployment_id() -> str:
    return require_env("WATSONX_AUTOAI_DEPLOYMENT_ID")


def get_server_name() -> str:
    return SERVER_NAME


def get_tool_name() -> str:
    return TOOL_NAME


@lru_cache(maxsize=1)
def _fetch_deployment_schema() -> tuple[list[dict[str, Any]], str]:
    """
    Fetches INPUT_FIELDS and PREDICTION_COLUMN from the watsonx API on first call.
    The result is cached for the lifetime of the process — the API is queried only once.
    """
    client = prepare_api_client()
    deployment_id = get_autoai_deployment_id()

    deployment_details = client.deployments.get_details(deployment_id)
    asset_id = _get_model_asset_id(deployment_details)
    asset_details = client.repository.get_model_details(asset_id)

    input_fields = _extract_input_fields(asset_details)
    label_column = _extract_label_column(asset_details)

    return input_fields, label_column


def _get_model_asset_id(deployment_details: dict[str, Any]) -> str:
    entity = deployment_details.get("entity", {})
    asset_id = entity.get("asset", {}).get("id")
    if not asset_id:
        raise RuntimeError(
            "Could not read entity.asset.id from deployment_details. "
            "Dump deployment_details to JSON and inspect the structure manually."
        )
    return asset_id


def _extract_input_fields(asset_details: dict[str, Any]) -> list[dict[str, Any]]:
    entity = asset_details.get("entity", {})
    schemas = entity.get("schemas") or entity.get("wml_model", {}).get("schemas")
    if not schemas or "input" not in schemas or not schemas["input"]:
        raise RuntimeError(
            "Input schema not found in model metadata. Dump "
            "asset_details to JSON, locate the input schema and adjust "
            "_extract_input_fields()."
        )
    return schemas["input"][0]["fields"]


def _extract_label_column(asset_details: dict[str, Any]) -> str:
    entity = asset_details.get("entity", {})
    label_column = entity.get("label_column") or entity.get("wml_model", {}).get(
        "label_column"
    )
    if not label_column:
        raise RuntimeError(
            "label_column not found in model metadata. Dump "
            "asset_details to JSON, locate the target column and adjust "
            "_extract_label_column()."
        )
    return label_column


def get_input_fields() -> list[dict[str, Any]]:
    fields, _ = _fetch_deployment_schema()
    return fields


def get_prediction_column() -> str:
    _, label_column = _fetch_deployment_schema()
    return label_column


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
    model_fields: dict[str, tuple[type, Any]] = {}

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
