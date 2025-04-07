from typing import Callable, TYPE_CHECKING

from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from ibm_cloud_sdk_core.authenticators import BearerTokenAuthenticator
from ibm_secrets_manager_sdk.secrets_manager_v2 import SecretsManagerV2

if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient


def tavily_search_watsonx(
    api_client: "APIClient",
    service_manager_service_url: str,
    secret_id: str,
) -> Callable:

    authenticator = BearerTokenAuthenticator(api_client.token)

    secretsManager = SecretsManagerV2(authenticator=authenticator)

    secretsManager.set_service_url(service_url=service_manager_service_url)

    response = secretsManager.get_secret(id=secret_id)

    tavily_search_tool = TavilySearch(
        max_results=2,
        topic="general",
        tavily_api_key=response.result["data"]["tavily_api_key"],
    )

    @tool("search", parse_docstring=True)
    def tavily_search(query: str) -> str:
        """
        Search tool aimed at efficient, quick and persistent search results.

        Args:
            query: User query to search using tavily.

        Returns:
            String of search results.
        """
        response = tavily_search_tool.invoke({"query": query})
        joined_content = "\n".join([el["content"] for el in response["results"]])

        return joined_content

    return tavily_search
