"""Scripts for creating knowledge graph with vector representation from the provided text."""

import os

from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ibm import ChatWatsonx, WatsonxEmbeddings
from ibm_watsonx_ai import APIClient, Credentials

from dotenv import load_dotenv
from utils import load_config

load_dotenv()

# Load config.toml
config = load_config()
dep_config_online_parameters = config["deployment"]["online"]["parameters"]

# Model ids
WATSONX_MODEL_ID = dep_config_online_parameters["model_id"]
WATSONX_EMBEDDING_MODEL_ID = dep_config_online_parameters["embedding_model_id"]

# Define APIClient using env variables
api_client = APIClient(
    credentials=Credentials(
        url=os.environ.get("WATSONX_URL"),
        api_key=os.environ.get("WATSONX_APIKEY"),
        token=os.environ.get("WATSONX_TOKEN"),
    ),
    space_id=os.environ.get("WATSONX_SPACE_ID"),
    project_id=os.environ.get("WATSONX_PROJECT_ID"),
)


# Define llm and embedding models
llm = ChatWatsonx(model_id=WATSONX_MODEL_ID, watsonx_client=api_client, temperature=0)
embedding_func = WatsonxEmbeddings(
    model_id=WATSONX_EMBEDDING_MODEL_ID,
    watsonx_client=api_client,
    params={"truncate_input_tokens": 512},
)


def prepare_documents(documents: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=256)
    return text_splitter.split_documents(documents)


def create_knowledge_graph(graph_documents: list[GraphDocument]) -> Neo4jGraph:
    # By default, url, username and password are read from env variables
    graph = Neo4jGraph(refresh_schema=False)
    graph.add_graph_documents(
        graph_documents=graph_documents, baseEntityLabel=True, include_source=True
    )

    #  Create full text index for graph traversal
    graph.query(
        "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]"
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


if __name__ == "__main__":
    # Example text
    text = """
    Marie Curie, born in 1867, was a Polish and naturalised-French physicist and chemist who conducted pioneering research on radioactivity.
    She was the first woman to win a Nobel Prize, the first person to win a Nobel Prize twice, and the only person to win a Nobel Prize in two scientific fields.
    Her husband, Pierre Curie, was a co-winner of her first Nobel Prize, making them the first-ever married couple to win the Nobel Prize and launching the Curie family legacy of five Nobel Prizes.
    She was, in 1906, the first woman to become a professor at the University of Paris.
    """

    documents = [Document(page_content=text)]

    chunks = prepare_documents(documents)

    # Experimental LLM graph transformer that generates graph documents
    llm_transformer = LLMGraphTransformer(llm=llm)
    graph_documents = llm_transformer.convert_to_graph_documents(chunks)

    neo4j_graph = create_knowledge_graph(graph_documents=graph_documents)
    create_vector_index_from_graph(neo4j_graph)
