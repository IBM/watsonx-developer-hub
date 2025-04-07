from typing import Callable, TYPE_CHECKING
from typing import Any, List

from langchain_core.tools import tool
# from langchain_core.retrievers import BaseRetriever
# from langchain.tools.retriever import create_retriever_tool
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_ibm import ChatWatsonx


if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient


# class NL2SQLRetriever(BaseRetriever):

#     def _get_relevant_documents(
#             self, query: str, *, run_manager: CallbackManagerForRetrieverRun
#             ) -> List[Document]:
#         """
#     Retrieve relevant documents based on a natural language query from a postgres database.

#     Args:
#         query (str): The query to search for relevant documents.

#     Returns:
#         List[Document]: A list of relevant documents retrieved based on the query.
#     """

#         llm = ChatWatsonx(
#             model_id="meta-llama/llama-3-3-70b-instruct",
#             url="https://us-south.ml.cloud.ibm.com",
#             project_id=os.getenv("PROJECT_ID"),
#             params={
#                 "decoding_method": "greedy",
#                 "max_new_tokens": 1000,
#                 "min_new_tokens": 1,
#             },
#         )


#         db_uri = os.getenv("PG_URI")
#         db = SQLDatabase.from_uri(db_uri)
#         chain = create_sql_query_chain(llm, db)
#         response = chain.invoke({"question": query})

#         return [Document(page_content=response)]

# def create_sql_retriever_tool(name = "sql_retrieve_documents", description = "Search and return information from SQL database"):
#     retriever = NL2SQLRetriever()
#     retriever_tool = create_retriever_tool(
#         retriever,
#         name,
#         description,
#     )
#     return retriever_tool

def sql_retriever_tool_watsonx(
    api_client: "APIClient",
) -> Callable:

    db_uri = ""
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