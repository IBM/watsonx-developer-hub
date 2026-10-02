import json
import logging
import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from pydantic import BaseModel, Field, create_model

# Loaded once at module import — in Orchestrate runtime the variables come
# from toolkit.yaml `env:` anyway, and load_dotenv() is a no-op when .env is absent.
load_dotenv()

logger = logging.getLogger(__name__)

SERVER_NAME = "auto-prediction-generic-toolkit"
TOOL_NAME = "get_auto_prediction"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not set")
    return value


@lru_cache(maxsize=1)
def prepare_api_client() -> APIClient:
    return APIClient(
        credentials=Credentials(
            url=require_env("WATSONX_URL"),
            api_key=require_env("WATSONX_API_KEY"),
        ),
        space_id=require_env("WATSONX_SPACE_ID"),
    )


def get_deployment_id() -> str:
    return require_env("WATSONX_DEPLOYMENT_ID")


def get_server_name() -> str:
    return SERVER_NAME


def get_tool_name() -> str:
    return TOOL_NAME


@lru_cache(maxsize=1)
def _fetch_deployment_schema() -> tuple[list[dict[str, Any]], str]:
    """
    Fetches INPUT_FIELDS and PREDICTION_COLUMN from the watsonx API on first call.
    The result is cached for the lifetime of the process — the API is queried only once.

    The repository method used to fetch asset details is chosen automatically
    based on ``entity.deployed_asset_type`` in the deployment response:
      - "model"      → client.repository.get_model_details()
      - "function"   → client.repository.get_function_details()
      - "ai_service" → client.repository.get_ai_service_details()
    """
    client = prepare_api_client()
    deployment_id = get_deployment_id()

    deployment_details = client.deployments.get_details(deployment_id)
    asset_id = _get_model_asset_id(deployment_details)
    deployed_asset_type = _get_deployed_asset_type(deployment_details)
    logger.debug(
        "deployed_asset_type=%r for deployment %s", deployed_asset_type, deployment_id
    )

    asset_details = _fetch_asset_details(client, asset_id, deployed_asset_type)

    input_fields = _extract_input_fields(asset_details)
    label_column = _extract_label_column(asset_details)

    return input_fields, label_column


# Mapping from deployed_asset_type values to the repository client method name.
_ASSET_TYPE_TO_REPO_METHOD: dict[str, str] = {
    "model": "get_model_details",
    "function": "get_function_details",
    "ai_service": "get_ai_service_details",
}


def _get_model_asset_id(deployment_details: dict[str, Any]) -> str:
    entity = deployment_details.get("entity", {})
    asset_id = entity.get("asset", {}).get("id")
    if not asset_id:
        raise RuntimeError(
            "Could not read entity.asset.id from deployment_details. "
            "Dump deployment_details to JSON and inspect the structure manually."
        )
    return asset_id


def _get_deployed_asset_type(deployment_details: dict[str, Any]) -> str:
    """Return the normalised deployed_asset_type string (lower-case, stripped)."""
    entity = deployment_details.get("entity", {})
    return str(entity.get("deployed_asset_type", "model")).lower().strip()


def _fetch_asset_details(
    client: APIClient,
    asset_id: str,
    deployed_asset_type: str,
) -> dict[str, Any]:
    """Call the correct repository method based on *deployed_asset_type*.

    Supported values: ``"model"``, ``"function"``, ``"ai_service"``.
    Falls back to ``get_model_details`` for unknown types and logs a warning.
    """
    method_name = _ASSET_TYPE_TO_REPO_METHOD.get(deployed_asset_type)
    if method_name is None:
        logger.warning(
            "Unknown deployed_asset_type %r — falling back to get_model_details. "
            "Add an entry to _ASSET_TYPE_TO_REPO_METHOD if this is incorrect.",
            deployed_asset_type,
        )
        method_name = "get_model_details"

    repo_method = getattr(client.repository, method_name)
    try:
        return repo_method(asset_id)
    except Exception as error:
        raise RuntimeError(
            f"Failed to fetch asset details for asset_id={asset_id!r} "
            f"using client.repository.{method_name}() "
            f"(deployed_asset_type={deployed_asset_type!r}). "
            f"Original error: {error}"
        ) from error


def _input_fields_from_env() -> list[dict[str, Any]] | None:
    """Return input fields from DEPLOYMENT_INPUT_FIELDS env var, or None if not set."""
    raw = os.getenv("DEPLOYMENT_INPUT_FIELDS", "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "DEPLOYMENT_INPUT_FIELDS is set but is not valid JSON. "
            "Expected a JSON array of field objects, e.g.: "
            '[{"name":"age","type":"integer"},{"name":"city","type":"string"}]. '
            f"Parse error: {exc}"
        ) from exc
    if not isinstance(parsed, list):
        raise ValueError(
            "DEPLOYMENT_INPUT_FIELDS must be a JSON array of field objects, "
            f"got {type(parsed).__name__}."
        )
    return parsed


def _extract_input_fields(asset_details: dict[str, Any]) -> list[dict[str, Any]]:
    entity = asset_details.get("entity", {})
    schemas = entity.get("schemas") or entity.get("wml_model", {}).get("schemas")
    fields: list[dict[str, Any]] | None = None

    if schemas and "input" in schemas and schemas["input"]:
        first_input = schemas["input"][0]
        if "fields" in first_input:
            fields = first_input["fields"]

    if fields is not None:
        return fields

    # Asset metadata is missing the schema — try the env-var fallback.
    env_fields = _input_fields_from_env()
    if env_fields is not None:
        logger.warning(
            "Input schema not found in asset metadata. "
            "Using DEPLOYMENT_INPUT_FIELDS from environment variables."
        )
        return env_fields

    raise RuntimeError(
        "Input schema not found in asset metadata and DEPLOYMENT_INPUT_FIELDS is not set.\n"
        "To fix this, set the following variable in your environment (or .env file) "
        "and restart the server:\n\n"
        '    DEPLOYMENT_INPUT_FIELDS=\'[{"name":"field1","type":"string"}]\'\n\n'
        "Replace the example with the actual input fields for your deployment."
    )


def _extract_label_column(asset_details: dict[str, Any]) -> str:
    entity = asset_details.get("entity", {})
    label_column = entity.get("label_column") or entity.get("wml_model", {}).get(
        "label_column"
    )

    if label_column:
        return label_column

    # Asset metadata is missing label_column — try the env-var fallback.
    env_label = os.getenv("DEPLOYMENT_LABEL_COLUMN", "").strip()
    if env_label:
        logger.warning(
            "label_column not found in asset metadata. "
            "Using DEPLOYMENT_LABEL_COLUMN from environment variables."
        )
        return env_label

    raise RuntimeError(
        "label_column not found in asset metadata and DEPLOYMENT_LABEL_COLUMN is not set.\n"
        "To fix this, set the following variable in your environment (or .env file) "
        "and restart the server:\n\n"
        "    DEPLOYMENT_LABEL_COLUMN=your_target_column\n\n"
        "Replace 'your_target_column' with the actual prediction target for your deployment."
    )


def get_input_fields() -> list[dict[str, Any]]:
    fields, _ = _fetch_deployment_schema()
    return list(fields)


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

    return create_model("DeploymentInput", **model_fields)


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


def extract_prediction(
    response: dict[str, Any], prediction_column: str | None = None
) -> dict[str, Any]:
    """Parse the deployment scoring response into a structured result.

    Returns a dict with two keys:
    - ``"prediction"``  – the scalar value of the target column (or the full
                          values list when the column cannot be identified).
    - ``"all_fields"``  – ordered dict mapping every response field name to
                          its value so callers have the full row available.

    Example response shape expected from watsonx.ai::

        {'predictions': [{'fields': ['Gender', 'Status', ..., 'Prediction', 'Probability'],
                          'values': [['Male', 'M', ..., 1, 0.9]]}]}
    """
    try:
        prediction_block = response["predictions"][0]
        fields: list[str] = prediction_block.get("fields", [])
        values: list[Any] = prediction_block["values"][0]
    except (KeyError, IndexError, TypeError) as error:
        logger.debug("Unexpected deployment response: %s", response)
        predictions = (
            response.get("predictions") if isinstance(response, dict) else None
        )
        safe_summary = (
            f"top-level keys={list(response.keys())}, predictions length={len(predictions)}"
            if isinstance(response, dict) and predictions is not None
            else f"response type={type(response).__name__}"
        )
        raise RuntimeError(
            f"Unexpected response structure from deployment: {safe_summary}"
        ) from error

    # Build a named mapping of every field returned by the model.
    all_fields: dict[str, Any] = dict(zip(fields, values)) if fields else {}

    # Identify the scalar prediction value.
    # Priority: (1) field matching prediction_column, (2) field named
    # "Prediction" / "prediction", (3) fall back to the raw values list.
    predicted_value: Any
    if prediction_column and prediction_column in all_fields:
        predicted_value = all_fields[prediction_column]
    else:
        # Try common default names used by watsonx.ai scoring responses.
        for candidate in ("Prediction", "prediction"):
            if candidate in all_fields:
                predicted_value = all_fields[candidate]
                break
        else:
            # Last resort: single value or full list.
            predicted_value = values[0] if len(values) == 1 else values

    return {
        "prediction": predicted_value,
        "all_fields": all_fields,
    }
