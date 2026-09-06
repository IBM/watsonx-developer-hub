from typing import TYPE_CHECKING

from ibm_watsonx_ai.foundation_models import Embeddings
from ibm_watsonx_ai.foundation_models.extensions.rag import VectorStore
from langchain_core.tools import BaseTool, tool

if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient


def retriever_tool_watsonx(
    api_client: "APIClient",
    embedding_model_id: str,
    vector_store_connection_id: str,
    vector_store_index_name: str,
) -> BaseTool:
    embeddings = Embeddings(model_id=embedding_model_id, api_client=api_client)

    vector_store = VectorStore(
        api_client=api_client,
        connection_id=vector_store_connection_id,
        embeddings=embeddings,
        index_name=vector_store_index_name,
    )

    @tool("retriever", parse_docstring=True)
    def retriever_tool(query: str) -> str:
        """
        Vector Store Index retriever tool.

        Args:
            query: User query related to information stored in Vector Index.

        Returns:
            Retrieved chunk.
        """
        return vector_store.search(query, 1)[0].page_content

    return retriever_tool
