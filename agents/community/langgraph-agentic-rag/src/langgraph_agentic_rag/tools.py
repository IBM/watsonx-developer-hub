from typing import Callable, TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient


def retriever_tool_watsonx(
    api_client: "APIClient",
    tool_config: dict,
) -> Callable:

    from langchain_ibm.toolkit import WatsonxToolkit

    toolkit = WatsonxToolkit(watsonx_client=api_client)

    rag_tool = toolkit.get_tool("RAGQuery")
    rag_tool.set_tool_config(tool_config)

    @tool("retriever", parse_docstring=True)
    def retriever_tool(query: str) -> str:
        """
        Vector Store Index retriever tool.

        Args:
            query: User query related to information stored in Vector Index.

        Returns:
            Retrieved chunk.
        """
        return rag_tool.invoke({"input": query})["output"]

    return retriever_tool
