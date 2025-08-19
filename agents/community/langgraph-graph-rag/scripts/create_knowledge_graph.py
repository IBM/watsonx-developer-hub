import os

from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ibm import ChatWatsonx, WatsonxEmbeddings
from ibm_watsonx_ai import APIClient, Credentials

from dotenv import load_dotenv

load_dotenv()

api_client = APIClient(
    credentials=Credentials(
        url=os.environ.get("WATSONX_URL"),
        api_key=os.environ.get("WATSONX_APIKEY"),
        token=os.environ.get("WATSONX_TOKEN"),
    ),
    space_id=os.environ.get("WATSONX_SPACE_ID"),
    project_id=os.environ.get("WATSONX_PROJECT_ID"),
)

WATSONX_MODEL_ID = "mistralai/mistral-medium-2505"
WATSONX_EMBEDDING_MODEL_ID = "ibm/slate-125m-english-rtrvr-v2"

llm = ChatWatsonx(model_id=WATSONX_MODEL_ID, watsonx_client=api_client, temperature=0)
embedding_func = WatsonxEmbeddings(
    model_id=WATSONX_EMBEDDING_MODEL_ID,
    watsonx_client=api_client,
    params={"truncate_input_tokens": 512},
)

llm_transformer = LLMGraphTransformer(llm=llm)


def prepare_documents(documents: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=256)
    return text_splitter.split_documents(documents)


def convert_documents_to_graph_documents(
    documents: list[Document],
) -> list[GraphDocument]:
    return llm_transformer.convert_to_graph_documents(documents)


def generate_knowledge_graph(graph_documents: list[GraphDocument]) -> Neo4jGraph:
    # By default, url, username and password are read from env variables
    graph = Neo4jGraph(refresh_schema=False)
    graph.add_graph_documents(
        graph_documents=graph_documents, baseEntityLabel=True, include_source=True
    )
    return graph


def create_vector_index_from_graph(graph: Neo4jGraph) -> None:
    _ = Neo4jVector.from_existing_graph(
        embedding=embedding_func,
        search_type="hybrid",
        node_label="Document",
        embedding_node_property="embedding",
        text_node_properties=["text"],
        graph=graph,
    )

    graph.query(
        "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity___) ON EACH [e.id]"
    )


if __name__ == "__main__":
    text = """
    
    """

    documents = [Document(page_content=text)]

    chunks = prepare_documents(documents)

    graph_documents = convert_documents_to_graph_documents(chunks)

    neo4j_graph = generate_knowledge_graph(graph_documents=graph_documents)
    create_vector_index_from_graph(neo4j_graph)
