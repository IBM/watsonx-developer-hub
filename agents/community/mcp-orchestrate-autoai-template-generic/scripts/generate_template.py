"""
Generates toolkit.yaml and agent.yaml based on the AutoAI deployment
specified by WATSONX_AUTOAI_DEPLOYMENT_ID.

Run from the template root directory:
    python scripts/generate_template.py

Requires a .env file in the root directory (copied from template.env).
"""

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
DEFAULT_AGENT_NAME = "autoai_prediction_agent"
DEFAULT_TOOL_NAME = "get_autoai_prediction"
DEFAULT_SERVER_NAME = "autoai-generic-toolkit"
DEFAULT_LLM_NAME = "groq/openai/gpt-oss-120b"


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


def get_model_asset_details(client: APIClient, asset_id: str) -> dict[str, Any]:
    """
    Fetches the metadata of the model backing the deployment.

    NOTE: an AutoAI deployment points to a MODEL asset in the repository,
    not to a data asset. `client.data_assets.get_details()` (used in a previous
    version of this code) was incorrect and failed for most WML instances.
    The correct call is `client.repository.get_model_details()`.
    """
    try:
        return client.repository.get_model_details(asset_id)
    except Exception as error:
        raise RuntimeError(
            f"Failed to fetch model details for asset_id={asset_id!r} "
            "via client.repository.get_model_details(). Verify that "
            "entity.asset.id in deployment_details actually points to "
            f"a model in the repository. Original error: {error}"
        ) from error


def get_input_fields(asset_details: dict[str, Any]) -> list[dict[str, Any]]:
    entity = asset_details.get("entity", {})
    schemas = entity.get("schemas") or entity.get("wml_model", {}).get("schemas")
    if not schemas or "input" not in schemas or not schemas["input"]:
        raise RuntimeError(
            "Input schema not found in model metadata. Dump "
            "asset_details to JSON, locate the input schema and adjust "
            "get_input_fields()."
        )
    return schemas["input"][0]["fields"]


def get_label_column(asset_details: dict[str, Any]) -> str:
    entity = asset_details.get("entity", {})
    label_column = entity.get("label_column") or entity.get("wml_model", {}).get(
        "label_column"
    )
    if not label_column:
        raise RuntimeError(
            "label_column not found in model metadata. Dump "
            "asset_details to JSON, locate the target column and adjust "
            "get_label_column()."
        )
    return label_column


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
        ],
        "tools": ["*"],
        "package_root": "./mcp_server",
    }


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
        "llm": DEFAULT_LLM_NAME,
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


def main() -> None:
    load_env()
    client = prepare_api_client()

    deployment_id = require_env("WATSONX_AUTOAI_DEPLOYMENT_ID")

    deployment_details = get_deployment_details(client, deployment_id)
    asset_id = get_model_asset_id(deployment_details)
    asset_details = get_model_asset_details(client, asset_id)

    input_fields = get_input_fields(asset_details)
    label_column = get_label_column(asset_details)

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
