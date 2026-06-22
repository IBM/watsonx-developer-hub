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

DEFAULT_TOOLKIT_NAME = "ai-services-toolkit-v1"
DEFAULT_AGENT_NAME = "ai_services_agent_v1"
DEFAULT_TOOL_NAME = "get_ai_service_response"
DEFAULT_SERVER_NAME = DEFAULT_TOOLKIT_NAME
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
    name = deployment_details.get("metadata", {}).get("name")
    if not name:
        raise RuntimeError(
            "Could not determine deployment name from deployment details"
        )
    return name


def get_deployment_description(deployment_details: dict[str, Any]) -> str:
    description = deployment_details.get("metadata", {}).get("description")

    return description if description else "Deployment has no description"


def get_ai_service_id(deployment_details: dict[str, Any]) -> str:
    ai_service_id = deployment_details["entity"]["asset"]["id"]

    return ai_service_id


def get_ai_service_details(client: APIClient, ai_service_id: str) -> dict[str, Any]:
    return client.repository.get_ai_service_details(ai_service_id)


def get_ai_service_name(ai_service_details: dict[str, Any]) -> str:
    name = ai_service_details.get("metadata", {}).get("name")
    if not name:
        raise RuntimeError(
            "Could not determine AI service name from AI service details"
        )
    return name


def get_ai_service_description(ai_service_details: dict[str, Any]) -> str:
    description = ai_service_details.get("metadata", {}).get("description")

    return description if description else "AI service has no description"


def build_metadata(
        deployment_id: str,
        deployment_name: str,
        deployment_description: str,
        ai_service_id: str,
        ai_service_name: str,
        ai_service_description: str,
) -> dict[str, Any]:
    return {
        "deployment_id": deployment_id,
        "deployment_name": deployment_name,
        "deployment_description": deployment_description,
        "ai_service_id": ai_service_id,
        "ai_service_name": ai_service_name,
        "ai_service_description": ai_service_description,
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
        f'DEPLOYMENT_DESCRIPTION = "{metadata["deployment_description"]}"\n'
        f'AI_SERVICE_ID = "{metadata["ai_service_id"]}"\n'
        f'AI_SERVICE_NAME = "{metadata["ai_service_name"]}"\n'
        f'AI_SERVICE_DESCRIPTION = "{metadata["ai_service_description"]}"\n'
    )
    with open(GENERATED_CONFIG_PATH, "w", encoding="utf-8") as file:
        file.write(content)


def build_toolkit_yaml() -> dict[str, Any]:
    return {
        "spec_version": "v1",
        "kind": "mcp",
        "name": DEFAULT_TOOLKIT_NAME,
        "description": "Generic watsonx.ai AI Services toolkit with deployed AI services as tools",
        "command": "python server.py",
        "env": [
            "WATSONX_URL",
            "WATSONX_API_KEY",
            "WATSONX_SPACE_ID",
            "WATSONX_AI_SERVICE_DEPLOYMENT_ID",
        ],
        "tools": ["*"],
        "package_root": "./mcp_server",
    }


def build_agent_yaml(deployment_name: str, deployment_description: str) -> dict[str, Any]:
    instructions = (
        "You are an assistant powered by deployed watsonx.ai AI services.\n\n"
        "STRICT RULES — follow these without exception:\n"
        "1. For user questions that require an answer from the knowledge base, ALWAYS call "
        f"{DEFAULT_TOOL_NAME}.\n"
        "2. Determine necessity to use a tool basing on a user request association with the name or description of the RAG Pattern AI service.\n"
        f"The name is: '{deployment_name}'. The description is: '{deployment_description}'\n"
        "3. If you are not sure, prefer calling "
        f"{DEFAULT_TOOL_NAME}.\n"
        "4. NEVER answer knowledge questions from your own knowledge when the RAG tool should be used.\n"
        "5. If the user asks whether the deployment is configured, available, or what deployment is being used, call "
        f"{DEFAULT_RAG_DEPLOYMENT_DETAILS_TOOL_NAME}.\n"
        "6. If a tool returns an error, explain the failure plainly and do not invent missing information.\n"
        "Your role is to route knowledge questions to the RAG Pattern AI service and use the diagnostics tool only for configuration or troubleshooting requests."
    )

    return {
        "spec_version": "v1",
        "kind": "native",
        "name": DEFAULT_AGENT_NAME,
        "description": (
            "Answers user questions using a watsonx.ai deployed AI service if needed."
        ),
        "llm": DEFAULT_LLM_NAME,
        "style": "react",
        "hide_reasoning": False,
        "instructions": instructions,
        "tools": [
            f"{DEFAULT_TOOLKIT_NAME}:{DEFAULT_TOOL_NAME}",
        ],
        "collaborators": [],
    }


class IndentedListDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow=flow, indentless=indentless)


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
    deployment_description = get_deployment_description(deployment_details)

    ai_service_id = get_ai_service_id(deployment_details)
    ai_service_details = get_ai_service_details(client, ai_service_id)
    ai_service_name = get_ai_service_name(ai_service_details)
    ai_service_description = get_ai_service_description(ai_service_details)

    metadata = build_metadata(
        deployment_id=deployment_id,
        deployment_name=deployment_name,
        deployment_description=deployment_description,
        ai_service_id=ai_service_id,
        ai_service_name=ai_service_name,
        ai_service_description=ai_service_description,
    )
    write_generated_config(metadata)

    toolkit_yaml = build_toolkit_yaml()
    agent_yaml = build_agent_yaml(deployment_name=deployment_name, deployment_description=deployment_description)

    write_yaml(TOOLKIT_PATH, toolkit_yaml)
    write_yaml(AGENT_PATH, agent_yaml)

    print(f"Generated {TOOLKIT_PATH}")
    print(f"Generated {AGENT_PATH}")
    print(f"Generated {GENERATED_CONFIG_PATH}")


if __name__ == "__main__":
    main()
