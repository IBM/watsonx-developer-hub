from typing import Callable, TYPE_CHECKING
from typing import Any, List

from ibm_cloud_sdk_core.authenticators.bearer_token_authenticator import BearerTokenAuthenticator
from ibm_secrets_manager_sdk.secrets_manager_v2 import SecretsManagerV2

from langchain_core.tools import tool
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_ibm import ChatWatsonx
from langchain_community.utilities import GoogleSerperAPIWrapper


if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient


def get_secret(api_client, secret_name):
    service_url = "https://a14f50a6-1721-4bd9-930c-403264d61ec1.au-syd.secrets-manager.appdomain.cloud"
    secretsManager = SecretsManagerV2(
        authenticator=BearerTokenAuthenticator(bearer_token=api_client.token),
    )

    secretsManager.set_service_url(service_url.format(instance_ID="insatnce_id"))

    # response = secretsManager.get_secret('1a3b9a7c-f133-b7ee-2b62-1421bbb3ea37')
    response = secretsManager.get_secret_by_name_type(
        secret_type='kv',
        name=secret_name,
        secret_group_name='default'
    )

    # secret = response.get_result()
    return response.result["data"][secret_name]


def sql_retriever_tool_watsonx(
    api_client: "APIClient",
) -> Callable:

    db_uri = get_secret(api_client, "PG_URI")
    db = SQLDatabase.from_uri(db_uri)
    model_id = "meta-llama/llama-3-3-70b-instruct"
    llm = ChatWatsonx(model_id=model_id, watsonx_client=api_client, disable_streaming = True)
    chain = create_sql_query_chain(llm, db)

    @tool("sql_retriever", parse_docstring=True)
    def sql_retriever_tool(query: str) -> str:
        """
        SQL retrieval tool for sustainability statistics for suppliers such as scope 1 and scope 2 carbon emmisions and revenue.

        Args:
            query: User query related to information stored in Vector Index.

        Returns:
            Retrieved chunk.
        """

        return chain.invoke({"question": query})

    return sql_retriever_tool



def retriever_tool_watsonx(
    api_client: "APIClient",
    tool_config: dict,
) -> Callable:

    from langchain_ibm.toolkit import WatsonxToolkit

    toolkit = WatsonxToolkit(watsonx_client=api_client)

    rag_tool = toolkit.get_tool("RAGQuery")
    rag_tool.set_tool_config(tool_config)

    @tool("vectordb_retriever", parse_docstring=True)
    def retriever_tool(query: str) -> str:
        """
        Vector Store Index retriever tool to retrieve sustainability reports.

        Args:
            query: User query related to information stored in Vector Index.

        Returns:
            Retrieved chunk.
        """
        return rag_tool.invoke({"input": query})["output"]

    return retriever_tool


def websearch_tool_watsonx(
    api_client: "APIClient",
    tool_config: dict,
) -> Callable:

    from langchain_ibm.toolkit import WatsonxToolkit

    toolkit = WatsonxToolkit(watsonx_client=api_client)
    rag_tool = toolkit.get_tool("GoogleSearch")
    rag_tool.set_tool_config(tool_config)

    @tool("websearch", parse_docstring=True)
    def websearch_tool(query: str) -> str:
        """
        Search for online trends, news, current events, real-time information, or research topics.

        Args:
            query: User query related to information on the internet.

        Returns:
            Retrieved chunk.
        """
        return rag_tool.invoke({"input": query})["output"]

    return websearch_tool


def serper_search_tool(
    api_client: "APIClient",
    # tool_config: dict,
) -> Callable:
    apikey = get_secret(api_client, "SERPER_APIKEY")
    serper_search = GoogleSerperAPIWrapper(serper_api_key=apikey)

    @tool("serpersearch", parse_docstring=True)
    def serper_search_tool(query: str) -> str:
        """
        Search for online trends, news, current events, real-time information, or research topics.

        Args:
            query: User query related to information on the internet.

        Returns:
            Retrieved chunk.
        """
        return serper_search.run(query)

    return serper_search_tool