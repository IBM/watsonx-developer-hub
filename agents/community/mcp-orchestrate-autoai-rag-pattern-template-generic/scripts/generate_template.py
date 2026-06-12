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

DEFAULT_TOOLKIT_NAME = "autoai-rag-pattern-toolkit"
DEFAULT_AGENT_NAME = "autoai_rag_pattern_agent"
DEFAULT_TOOL_NAME = "get_rag_pattern_answer"
DEFAULT_SERVER_NAME = "autoai-rag-pattern-toolkit"
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


def get_deployment_name(deployment_details: dict[str, Any]) -> str:
    metadata = deployment_details.get("metadata", {})
    name = metadata.get("name")
    if not name:
        raise RuntimeError(
            "Could not determine deployment name from deployment details"
        )
    return name


def build_metadata(
    deployment_id: str,
    deployment_name: str,
) -> dict[str, Any]:
    return {
        "deployment_id": deployment_id,
        "deployment_name": deployment_name,
        "toolkit_name": DEFAULT_TOOLKIT_NAME,
        "tool_name": DEFAULT_TOOL_NAME,
        "agent_name": DEFAULT_AGENT_NAME,
        "server_name": DEFAULT_SERVER_NAME,
        "llm": DEFAULT_LLM_NAME,
    }


def write_generated_config(metadata: dict[str, Any]) -> None:
    content = (
        f'SERVER_NAME = "{metadata["server_name"]}"\n'
        f'TOOL_NAME = "{metadata["tool_name"]}"\n'
        f'DEPLOYMENT_NAME = "{metadata["deployment_name"]}"\n'
    )
    with open(GENERATED_CONFIG_PATH, "w", encoding="utf-8") as file:
        file.write(content)


def build_toolkit_yaml() -> dict[str, Any]:
    return {
        "spec_version": "v1",
        "kind": "mcp",
        "name": DEFAULT_TOOLKIT_NAME,
        "description": "Generic watsonx.ai AutoAI RAG Pattern toolkit",
        "command": "python server.py",
        "env": [
            "WATSONX_URL",
            "WATSONX_API_KEY",
            "WATSONX_SPACE_ID",
            "WATSONX_AUTOAI_RAG_PATTERN_DEPLOYMENT_ID",
        ],
        "tools": ["*"],
        "package_root": "./mcp_server",
    }


def build_agent_yaml(deployment_name: str) -> dict[str, Any]:
    instructions = (
        f"You are a question-answering assistant powered by the '{deployment_name}' AutoAI RAG Pattern AI service.\n\n"
        "STRICT RULES — follow these without exception:\n"
        "1. NEVER answer questions from your own knowledge or reasoning.\n"
        f"2. ALWAYS call {DEFAULT_TOOL_NAME} when the user asks a question.\n"
        "3. After the tool returns a result, present the answer clearly to the user.\n"
        "4. Do NOT make up answers or use your own knowledge.\n"
        "5. If the tool returns an error, inform the user and ask them to try again.\n\n"
        "Your role is to pass user questions to the RAG Pattern AI service and relay the responses."
    )

    return {
        "spec_version": "v1",
        "kind": "native",
        "name": DEFAULT_AGENT_NAME,
        "description": (
            f"Answers questions using the '{deployment_name}' watsonx.ai deployed AutoAI RAG Pattern AI service."
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

    deployment_id = require_env("WATSONX_AUTOAI_RAG_PATTERN_DEPLOYMENT_ID")

    deployment_details = get_deployment_details(client, deployment_id)
    deployment_name = get_deployment_name(deployment_details)

    metadata = build_metadata(
        deployment_id=deployment_id,
        deployment_name=deployment_name,
    )
    write_generated_config(metadata)

    toolkit_yaml = build_toolkit_yaml()
    agent_yaml = build_agent_yaml(deployment_name=deployment_name)

    write_yaml(TOOLKIT_PATH, toolkit_yaml)
    write_yaml(AGENT_PATH, agent_yaml)

    print(f"Generated {TOOLKIT_PATH}")
    print(f"Generated {AGENT_PATH}")
    print(f"Generated {GENERATED_CONFIG_PATH}")


if __name__ == "__main__":
    main()

# Made with Bob
