import os

from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials

from generated_config import DEPLOYMENT_NAME, SERVER_NAME, TOOL_NAME


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


def get_rag_deployment_id() -> str:
    load_env()
    deployment_id = os.getenv("WATSONX_AUTOAI_RAG_PATTERN_DEPLOYMENT_ID")
    if not deployment_id:
        raise ValueError("WATSONX_AUTOAI_RAG_PATTERN_DEPLOYMENT_ID is not set")
    return deployment_id


def get_server_name() -> str:
    return SERVER_NAME


def get_tool_name() -> str:
    return TOOL_NAME


def get_deployment_name() -> str:
    return DEPLOYMENT_NAME


# Made with Bob
