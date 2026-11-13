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

DEFAULT_TOOLKIT_NAME = "ai-services-toolkit-v3"
DEFAULT_AGENT_NAME = "ai_services_agent_v3"
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
    """
    Build toolkit YAML configuration.
    Supports both legacy single deployment ID and new multiple deployment IDs.
    """
    import os

    # Determine which env vars to include
    env_vars = [
        "WATSONX_URL",
        "WATSONX_API_KEY",
        "WATSONX_SPACE_ID",
    ]

    # Check if using legacy single ID or new multiple IDs
    if os.getenv("WATSONX_AI_SERVICE_DEPLOYMENT_ID"):
        env_vars.append("WATSONX_AI_SERVICE_DEPLOYMENT_ID")
    else:
        # Add numbered deployment IDs
        index = 1
        while os.getenv(f"WATSONX_AI_SERVICE_DEPLOYMENT_ID_{index}"):
            env_vars.append(f"WATSONX_AI_SERVICE_DEPLOYMENT_ID_{index}")
            index += 1

    return {
        "spec_version": "v1",
        "kind": "mcp",
        "name": DEFAULT_TOOLKIT_NAME,
        "description": "Generic watsonx.ai AI Services toolkit with deployed AI service(s) as tool(s)",
        "command": "python server.py",
        "env": env_vars,
        "tools": ["*"],
        "package_root": "./mcp_server",
    }


def build_agent_yaml(
        deployments_info: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Build agent YAML configuration.

    Args:
        deployments_info: List of dicts containing deployment information
                         Each dict has: deployment_name, deployment_description,
                         ai_service_name, ai_service_description, tool_name
    """
    # Build the available services section
    services_list = []
    for idx, info in enumerate(deployments_info, 1):
        services_list.append(
            f"{idx}. {info['deployment_name']}\n"
            f"   - Description: {info['deployment_description']}\n"
            f"   - AI Service: {info['ai_service_name']}\n"
            f"   - Tool: {info['tool_name']}"
        )

    services_text = "\n".join(services_list)

    instructions = (
        "You are an assistant powered by deployed watsonx.ai AI services.\n\n"
        "AVAILABLE AI SERVICES:\n"
        f"{services_text}\n\n"
        "STRICT RULES — follow these without exception:\n"
        "1. When the user says hello or asks what you can do, list the available tools and briefly explain their purpose and required inputs.\n"
        "2. ONLY call an AI service tool when the user's request is clearly related to that specific deployment or AI service based on their names and descriptions above.\n"
        "3. If one or more required tool input fields are missing, ask only for the missing fields.\n"
        "4. Analyze the user's request carefully:\n"
        "   - If it matches the purpose described in a deployment/service description, use that tool\n"
        "   - If it's a general question unrelated to any AI service's purpose, answer from your own knowledge\n"
        "   - When in doubt about relevance, ask the user for clarification rather than calling a tool\n"
        "5. If a tool returns an error, explain the failure clearly and do not invent missing information.\n"
        "6. When a tool returns a result, retrieve only helpful data based on the user's request and provide them to the user.\n"
        "7. Be helpful and conversational, but precise about when to use each AI service tool.\n"
        "8. If multiple services could handle a request, choose the most appropriate one or ask the user which they prefer.\n\n"
        "Your role is to intelligently route requests to the appropriate AI service only when relevant, based on each service's documented purpose."
    )

    # Build tools list
    tools = [f"{DEFAULT_TOOLKIT_NAME}:{info['tool_name']}" for info in deployments_info]

    return {
        "spec_version": "v1",
        "kind": "native",
        "name": DEFAULT_AGENT_NAME,
        "description": (
            "Answers user questions using watsonx.ai deployed AI services when appropriate."
        ),
        "llm": DEFAULT_LLM_NAME,
        "style": "react",
        "hide_reasoning": False,
        "instructions": instructions,
        "tools": tools,
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


def get_all_deployment_ids() -> dict[str, str]:
    """
    Get all deployment IDs from environment variables.
    Supports both legacy single ID and new multiple ID format.

    Returns:
        Dictionary mapping deployment index/name to deployment ID
    """
    import os

    deployment_ids = {}

    # Check for legacy single deployment ID
    single_id = os.getenv("WATSONX_AI_SERVICE_DEPLOYMENT_ID")
    if single_id:
        deployment_ids["default"] = single_id
        return deployment_ids

    # Check for numbered deployment IDs
    index = 1
    while True:
        env_var = f"WATSONX_AI_SERVICE_DEPLOYMENT_ID_{index}"
        deployment_id = os.getenv(env_var)
        if not deployment_id:
            break
        deployment_ids[str(index)] = deployment_id
        index += 1

    if not deployment_ids:
        raise ValueError(
            "No deployment IDs found. Set either WATSONX_AI_SERVICE_DEPLOYMENT_ID "
            "or WATSONX_AI_SERVICE_DEPLOYMENT_ID_1, WATSONX_AI_SERVICE_DEPLOYMENT_ID_2, etc."
        )

    return deployment_ids


def main() -> None:
    load_env()
    client = prepare_api_client()

    # Get all deployment IDs
    deployment_ids = get_all_deployment_ids()

    print(f"Found {len(deployment_ids)} deployment ID(s)")

    # Collect information for all deployments
    deployments_info = []
    all_metadata = []

    for index, deployment_id in deployment_ids.items():
        print(f"\nProcessing deployment {index}: {deployment_id}")

        deployment_details = get_deployment_details(client, deployment_id)
        deployment_name = get_deployment_name(deployment_details)
        deployment_description = get_deployment_description(deployment_details)

        ai_service_id = get_ai_service_id(deployment_details)
        ai_service_details = get_ai_service_details(client, ai_service_id)
        ai_service_name = get_ai_service_name(ai_service_details)
        ai_service_description = get_ai_service_description(ai_service_details)

        # Determine tool name
        if index == "default":
            tool_name = DEFAULT_TOOL_NAME
        else:
            tool_name = f"{DEFAULT_TOOL_NAME}_{index}"

        metadata = build_metadata(
            deployment_id=deployment_id,
            deployment_name=deployment_name,
            deployment_description=deployment_description,
            ai_service_id=ai_service_id,
            ai_service_name=ai_service_name,
            ai_service_description=ai_service_description,
        )
        all_metadata.append(metadata)

        deployments_info.append(
            {
                "deployment_name": deployment_name,
                "deployment_description": deployment_description,
                "ai_service_name": ai_service_name,
                "ai_service_description": ai_service_description,
                "tool_name": tool_name,
            }
        )

    # Write generated config for the first deployment (for backward compatibility)
    # In a multi-deployment scenario, this serves as a reference
    write_generated_config(all_metadata[0])

    toolkit_yaml = build_toolkit_yaml()
    agent_yaml = build_agent_yaml(deployments_info)

    write_yaml(TOOLKIT_PATH, toolkit_yaml)
    write_yaml(AGENT_PATH, agent_yaml)

    print(f"\nGenerated {TOOLKIT_PATH}")
    print(f"Generated {AGENT_PATH}")
    print(f"Generated {GENERATED_CONFIG_PATH}")
    print(f"\nTotal deployments configured: {len(deployment_ids)}")


if __name__ == "__main__":
    main()
