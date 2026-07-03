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

DEFAULT_TOOLKIT_NAME = "ai-services-toolkit-v2"
DEFAULT_AGENT_NAME = "ai_services_agent_v2"
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
        "description": "Generic watsonx.ai AI Services toolkit with deployed AI service as a tool",
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


def build_agent_yaml(
        deployment_name: str,
        deployment_description: str,
        ai_service_name: str,
        ai_service_description: str,
) -> dict[str, Any]:
    instructions = (
        "You are an assistant powered by deployed watsonx.ai AI services.\n\n"
        "AVAILABLE AI SERVICE:\n"
        f"- Deployment Name: {deployment_name}\n"
        f"- Deployment Description: {deployment_description}\n"
        f"- AI Service Name: {ai_service_name}\n"
        f"- AI Service Description: {ai_service_description}\n\n"
        "STRICT RULES — follow these without exception:\n"
        "1. When the user says hello or asks what you can do, list the available tools and briefly explain their purpose and required inputs.\n"
        "2. ONLY call the AI service tool when the user's request is clearly related to the deployment or AI service based on their names and descriptions above.\n"
        "3. If one or more required tool input fields are missing, ask only for the missing fields.\n"
        "4. Analyze the user's request carefully:\n"
        "   - If it matches the purpose described in the deployment/service descriptions, use the tool\n"
        "   - If it's a general question unrelated to the AI service's purpose, answer from your own knowledge\n"
        "   - When in doubt about relevance, ask the user for clarification rather than calling the tool\n"
        "5. If a tool returns an error, explain the failure clearly and do not invent missing information.\n"
        "6. When the tool returns a result, retrieve only helpful data based on a user's request and provide them to the user.\n"
        "7. Be helpful and conversational, but precise about when to use the AI service tool.\n\n"
        "Your role is to intelligently route requests to the AI service only when appropriate, based on the service's documented purpose."
    )

    return {
        "spec_version": "v1",
        "kind": "native",
        "name": DEFAULT_AGENT_NAME,
        "description": (
            "Answers user questions using a watsonx.ai deployed AI service when appropriate."
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

    deployment_id = require_env("WATSONX_AI_SERVICE_DEPLOYMENT_ID")

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
    agent_yaml = build_agent_yaml(
        deployment_name=deployment_name,
        deployment_description=deployment_description,
        ai_service_name=ai_service_name,
        ai_service_description=ai_service_description,
    )

    write_yaml(TOOLKIT_PATH, toolkit_yaml)
    write_yaml(AGENT_PATH, agent_yaml)

    print(f"Generated {TOOLKIT_PATH}")
    print(f"Generated {AGENT_PATH}")
    print(f"Generated {GENERATED_CONFIG_PATH}")


if __name__ == "__main__":
    main()
