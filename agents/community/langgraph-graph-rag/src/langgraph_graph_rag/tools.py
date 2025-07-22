from typing import Callable, TYPE_CHECKING

from langchain_core.tools import tool

from langchain_ibm import WatsonxEmbeddings

from langchain_neo4j import Neo4jVector


if TYPE_CHECKING:
    from ibm_watsonx_ai import APIClient

def retriever_tool_watsonx(
    api_client: "APIClient",
) -> Callable:

    embedding = WatsonxEmbeddings(watsonx_client=api_client, model_id="ibm/slate-125m-english-rtrvr-v2")
    neo4j_vector_index = Neo4jVector.from_existing_graph(
        embedding = embedding,
        url="bolt://localhost:7687", username="neo4j", password="password",
        index_name = 'title_abstract_vector',
        node_label = 'Article',
        text_node_properties = ['title', 'abstract'],
        embedding_node_property = 'embedding_vectors',
    )
    neo4j_retriever = neo4j_vector_index.as_retriever(search_kwargs={'k':3})

    @tool("retriever", parse_docstring=True)
    def retriever_tool(query: str) -> str:
        """
        Graph Vector Store retriever tool.

        Args:
            query: User query related to information stored in Graph database.

        Returns:
            Retrieved chunk.
        """
        return "\n\n".join([doc.page_content for doc in neo4j_retriever.invoke(query)])

    return retriever_tool
