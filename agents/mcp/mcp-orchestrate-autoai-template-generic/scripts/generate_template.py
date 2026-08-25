"""
Generates toolkit.yaml and agent.yaml based on the AutoAI deployment
specified by WATSONX_AUTOAI_DEPLOYMENT_ID.

Run from the template root directory:
    python scripts/generate_template.py

Requires a .env file in the root directory (copied from template.env).

Fallback behaviour
------------------
If the model asset referenced by WATSONX_AUTOAI_DEPLOYMENT_ID does not
expose ``input_fields`` or ``label_column`` in its metadata (e.g. the
deployment was created outside of AutoAI or the schema was stripped),
the script falls back to two optional environment variables:

    AUTOAI_INPUT_FIELDS  – JSON array of field descriptors, e.g.:
                           '[{"name":"age","type":"integer"},{"name":"city","type":"string"}]'
    AUTOAI_LABEL_COLUMN  – name of the target / prediction column, e.g.:
                           "risk"

Set both variables in your .env file before running the script again when
the model does not carry the required metadata.
"""

import json
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials

ROOT_DIR = Path(__file__).resolve().parent.parent
TOOLKIT_PATH = ROOT_DIR / "toolkit.yaml"
AGENT_PATH = ROOT_DIR / "agent.yaml"

DEFAULT_TOOLKIT_NAME = "autoai-generic-toolkit"
DEFAULT_SERVER_NAME = "autoai-generic-toolkit"
DEFAULT_AGENT_NAME = "autoai_prediction_agent"
DEFAULT_TOOL_NAME = "get_autoai_prediction"
DEFAULT_LLM_FALLBACK = "groq/openai/gpt-oss-120b"


def load_env() -> None:
    load_dotenv(ROOT_DIR / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"{name} is not set. Copy template.env to .env and fill in the values."
        )
    return value


def prepare_api_client() -> APIClient:
    return APIClient(
        credentials=Credentials(
            url=require_env("WATSONX_URL"),
            api_key=require_env("WATSONX_API_KEY"),
        ),
        space_id=require_env("WATSONX_SPACE_ID"),
    )


def get_deployment_details(client: APIClient, deployment_id: str) -> dict[str, Any]:
    return client.deployments.get_details(deployment_id)


# Mapping from deployed_asset_type values to the repository client method name.
_ASSET_TYPE_TO_REPO_METHOD: dict[str, str] = {
    "model": "get_model_details",
    "function": "get_function_details",
    "ai_service": "get_ai_service_details",
}


def get_model_asset_id(deployment_details: dict[str, Any]) -> str:
    entity = deployment_details.get("entity", {})
    asset = entity.get("asset", {})
    asset_id = asset.get("id")
    if not asset_id:
        raise RuntimeError(
            "Could not read entity.asset.id from deployment_details. "
            "Dump deployment_details to JSON and inspect the structure manually."
        )
    return asset_id


def get_deployed_asset_type(deployment_details: dict[str, Any]) -> str:
    """Return the normalised deployed_asset_type string (lower-case, stripped)."""
    entity = deployment_details.get("entity", {})
    return str(entity.get("deployed_asset_type", "model")).lower().strip()


def get_asset_details(
    client: APIClient,
    asset_id: str,
    deployed_asset_type: str,
) -> dict[str, Any]:
    """Fetch asset metadata using the repository method that matches *deployed_asset_type*.

    Supported values: ``"model"``, ``"function"``, ``"ai_service"``.
    Falls back to ``get_model_details`` for unknown types and prints a warning.
    """
    method_name = _ASSET_TYPE_TO_REPO_METHOD.get(deployed_asset_type)
    if method_name is None:
        print(
            f"⚠  Unknown deployed_asset_type {deployed_asset_type!r} — "
            "falling back to get_model_details. "
            "Add an entry to _ASSET_TYPE_TO_REPO_METHOD if this is incorrect."
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
    """Return input fields from AUTOAI_INPUT_FIELDS env var, or None if not set."""
    raw = os.getenv("AUTOAI_INPUT_FIELDS", "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "AUTOAI_INPUT_FIELDS is set but is not valid JSON. "
            "Expected a JSON array of field objects, e.g.: "
            '[{"name":"age","type":"integer"},{"name":"city","type":"string"}]. '
            f"Parse error: {exc}"
        ) from exc
    if not isinstance(parsed, list):
        raise ValueError(
            "AUTOAI_INPUT_FIELDS must be a JSON array of field objects, "
            f"got {type(parsed).__name__}."
        )
    return parsed


def get_input_fields(asset_details: dict[str, Any]) -> list[dict[str, Any]]:
    entity = asset_details.get("entity", {})
    schemas = entity.get("schemas") or entity.get("wml_model", {}).get("schemas")
    fields: list[dict[str, Any]] | None = None

    if schemas and "input" in schemas and schemas["input"]:
        first_input = schemas["input"][0]
        if "fields" in first_input:
            fields = first_input["fields"]

    if fields is not None:
        return fields

    # Model metadata is missing the schema — try the env-var fallback.
    env_fields = _input_fields_from_env()
    if env_fields is not None:
        print(
            "⚠  Input schema not found in model metadata. "
            "Using AUTOAI_INPUT_FIELDS from environment variables."
        )
        return env_fields

    raise RuntimeError(
        "Input schema not found in model metadata and AUTOAI_INPUT_FIELDS is not set.\n"
        "To fix this, add the following variable to your .env file and re-run:\n\n"
        '    AUTOAI_INPUT_FIELDS=\'[{"name":"field1","type":"string"}]\'\n\n'
        "Replace the example with the actual input fields for your model."
    )


def get_label_column(asset_details: dict[str, Any]) -> str:
    entity = asset_details.get("entity", {})
    label_column = entity.get("label_column") or entity.get("wml_model", {}).get(
        "label_column"
    )

    if label_column:
        return label_column

    # Model metadata is missing label_column — try the env-var fallback.
    env_label = os.getenv("AUTOAI_LABEL_COLUMN", "").strip()
    if env_label:
        print(
            "⚠  label_column not found in model metadata. "
            "Using AUTOAI_LABEL_COLUMN from environment variables."
        )
        return env_label

    raise RuntimeError(
        "label_column not found in model metadata and AUTOAI_LABEL_COLUMN is not set.\n"
        "To fix this, add the following variable to your .env file and re-run:\n\n"
        "    AUTOAI_LABEL_COLUMN=your_target_column\n\n"
        "Replace 'your_target_column' with the actual prediction target for your model."
    )


def build_toolkit_yaml() -> dict[str, Any]:
    return {
        "spec_version": "v1",
        "kind": "mcp",
        "name": DEFAULT_TOOLKIT_NAME,
        "description": "Generic watsonx.ai AutoAI prediction toolkit",
        "command": "python server.py",
        "env": [
            "WATSONX_URL",
            "WATSONX_API_KEY",
            "WATSONX_SPACE_ID",
            "WATSONX_AUTOAI_DEPLOYMENT_ID",
            # Optional fallback variables — required only when the model asset
            # does not expose input schema / label_column in its metadata.
            "AUTOAI_INPUT_FIELDS",
            "AUTOAI_LABEL_COLUMN",
        ],
        "tools": ["*"],
        "package_root": "./mcp_server",
    }


def get_llm_name() -> str:
    """Return LLM_NAME from the environment, falling back to DEFAULT_LLM_FALLBACK.

    Must be called after load_env() so that the .env file has been loaded.
    """
    return os.getenv("LLM_NAME", DEFAULT_LLM_FALLBACK)


def build_agent_yaml(
    label_column: str,
    input_fields: list[dict[str, Any]],
) -> dict[str, Any]:
    field_names = [field["name"] for field in input_fields]
    field_list = "\n".join([f"     - {name}" for name in field_names])

    instructions = (
        f"You are a prediction assistant for the '{label_column}' column.\n\n"
        "STRICT RULES — follow these without exception:\n"
        "1. NEVER answer prediction questions from your own knowledge or reasoning.\n"
        f"2. ALWAYS call {DEFAULT_TOOL_NAME} when the user provides all required input fields.\n"
        "3. If one or more required fields are missing, ask only for the missing fields.\n"
        "4. After the tool returns a result, report the prediction clearly.\n"
        "5. Do NOT perform your own calculations.\n\n"
        "Required input fields:\n"
        f"{field_list}"
    )

    return {
        "spec_version": "v1",
        "kind": "native",
        "name": DEFAULT_AGENT_NAME,
        "description": (
            f"Predicts the '{label_column}' column using a watsonx.ai deployed AutoAI model."
        ),
        "llm": get_llm_name(),
        "style": "react",
        "hide_reasoning": False,
        "instructions": instructions,
        "tools": [f"{DEFAULT_TOOLKIT_NAME}:{DEFAULT_TOOL_NAME}"],
        "collaborators": [],
    }


class IndentedListDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow=flow, indentless=False)


def write_yaml(path: Path, content: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(
            content,
            file,
            Dumper=IndentedListDumper,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            indent=2,
        )


def _format_fields(fields: list[dict[str, Any]], indent: int = 16) -> str:
    """Return a wrapped, aligned string of 'name (type)' pairs."""
    pad = " " * indent
    items = [f"{f['name']} ({f.get('type', 'unknown')})" for f in fields]
    lines: list[str] = []
    current = ""
    for item in items:
        candidate = f"{current}, {item}" if current else item
        if len(candidate) > 64 and current:
            lines.append(current)
            current = item
        else:
            current = candidate
    if current:
        lines.append(current)
    return f"\n{pad}".join(lines)


def main() -> None:
    load_env()
    client = prepare_api_client()

    deployment_id = require_env("WATSONX_AUTOAI_DEPLOYMENT_ID")
    print(f"Fetching deployment details for {deployment_id}...")

    deployment_details = get_deployment_details(client, deployment_id)
    asset_id = get_model_asset_id(deployment_details)
    deployed_asset_type = get_deployed_asset_type(deployment_details)
    print(f"✓ Found asset: {asset_id} (type: {deployed_asset_type})")

    print("Fetching asset metadata...")
    asset_details = get_asset_details(client, asset_id, deployed_asset_type)

    input_fields = get_input_fields(asset_details)
    label_column = get_label_column(asset_details)

    fields_str = _format_fields(input_fields)
    print(f"✓ Input fields:  {fields_str}")
    print(f"✓ Label column:  {label_column}")

    toolkit_yaml = build_toolkit_yaml()
    agent_yaml = build_agent_yaml(
        label_column=label_column,
        input_fields=input_fields,
    )

    write_yaml(TOOLKIT_PATH, toolkit_yaml)
    write_yaml(AGENT_PATH, agent_yaml)

    print(f"Generated {TOOLKIT_PATH}")
    print(f"Generated {AGENT_PATH}")


if __name__ == "__main__":
    main()
