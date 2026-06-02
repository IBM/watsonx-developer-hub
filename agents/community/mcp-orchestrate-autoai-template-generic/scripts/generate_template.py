from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials


ROOT_DIR = Path(__file__).resolve().parent.parent
MCP_SERVER_DIR = ROOT_DIR / "mcp_server"
GENERATED_CONFIG_PATH = MCP_SERVER_DIR / "generated_config.py"
TOOLKIT_PATH = ROOT_DIR / "toolkit.yaml"
AGENT_PATH = ROOT_DIR / "agent.yaml"

DEFAULT_TOOLKIT_NAME = "autoai-generic-toolkit"
DEFAULT_AGENT_NAME = "autoai_prediction_agent"
DEFAULT_TOOL_NAME = "get_autoai_prediction"
DEFAULT_SERVER_NAME = "autoai-generic-toolkit"
DEFAULT_LLM_NAME = "groq/openai/gpt-oss-120b"


def load_env() -> None:
    load_dotenv(ROOT_DIR / ".env")


def prepare_api_client() -> APIClient:
    return APIClient(
        credentials=Credentials(
            url=require_env("WATSONX_URL"),
            api_key=require_env("WATSONX_API_KEY"),
        ),
        space_id=require_env("WATSONX_SPACE_ID"),
    )


def require_env(name: str) -> str:
    import os

    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not set")
    return value


def get_deployment_details(client: APIClient, deployment_id: str) -> dict[str, Any]:
    return client.deployments.get_details(deployment_id)


def get_model_asset_id(deployment_details: dict[str, Any]) -> str:
    entity = deployment_details.get("entity", {})
    asset = entity.get("asset", {})
    asset_id = asset.get("id")
    if not asset_id:
        raise RuntimeError("Could not determine model asset id from deployment details")
    return asset_id


def get_model_asset_details(client: APIClient, asset_id: str) -> dict[str, Any]:
    return client.data_assets.get_details(asset_id)


def get_input_fields(asset_details: dict[str, Any]) -> list[dict[str, Any]]:
    schemas = asset_details["entity"]["wml_model"]["schemas"]
    return schemas["input"][0]["fields"]


def get_label_column(asset_details: dict[str, Any]) -> str:
    return asset_details["entity"]["wml_model"]["label_column"]


def build_metadata(
    deployment_id: str,
    input_fields: list[dict[str, Any]],
    label_column: str,
) -> dict[str, Any]:
    return {
        "deployment_id": deployment_id,
        "toolkit_name": DEFAULT_TOOLKIT_NAME,
        "tool_name": DEFAULT_TOOL_NAME,
        "agent_name": DEFAULT_AGENT_NAME,
        "server_name": DEFAULT_SERVER_NAME,
        "llm": DEFAULT_LLM_NAME,
        "label_column": label_column,
        "input_fields": input_fields,
    }


def write_generated_config(metadata: dict[str, Any]) -> None:
    content = (
        f'SERVER_NAME = "{metadata["server_name"]}"\n'
        f'TOOL_NAME = "{metadata["tool_name"]}"\n'
        f"TOOL_DESCRIPTION = \"Predict the value of '{metadata['label_column']}' using the deployed watsonx.ai AutoAI model. Provide all required input fields defined by the generated schema. Returns the prediction result from the deployment.\"\n"
        f'PREDICTION_COLUMN = "{metadata["label_column"]}"\n'
        f"INPUT_FIELDS = {repr(metadata['input_fields'])}\n"
    )
    with open(GENERATED_CONFIG_PATH, "w", encoding="utf-8") as file:
        file.write(content)


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

    metadata = build_metadata(
        deployment_id=deployment_id,
        input_fields=input_fields,
        label_column=label_column,
    )
    write_generated_config(metadata)

    toolkit_yaml = build_toolkit_yaml()
    agent_yaml = build_agent_yaml(
        label_column=label_column,
        input_fields=input_fields,
    )

    write_yaml(TOOLKIT_PATH, toolkit_yaml)
    write_yaml(AGENT_PATH, agent_yaml)

    print(f"Generated {TOOLKIT_PATH}")
    print(f"Generated {AGENT_PATH}")
    print(f"Generated {GENERATED_CONFIG_PATH}")


if __name__ == "__main__":
    main()
