from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool
from langchain_ibm import ChatWatsonx
from langchain_ibm.agent_toolkits.sql import WatsonxSQLDatabaseToolkit
from langchain_ibm.utilities.sql_database import WatsonxSQLDatabase

if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient


def sql_tools_watsonx(
    api_client: "APIClient",
    tool_config: dict,
) -> list[BaseTool]:

    chat_llm = ChatWatsonx(
        model_id=tool_config['model_id'],
        params={"temperature": 0.2},
        watsonx_client=api_client,
    )

    sql_database = WatsonxSQLDatabase(
        connection_id=tool_config['connection_id'], schema=tool_config['schema'], watsonx_client=api_client
    )
    sql_toolkit = WatsonxSQLDatabaseToolkit(db=sql_database, llm=chat_llm)

    return sql_toolkit.get_tools()
