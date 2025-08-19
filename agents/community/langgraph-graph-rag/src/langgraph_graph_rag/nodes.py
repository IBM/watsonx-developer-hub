from typing import Annotated, Sequence, Any

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

from langchain_ibm import ChatWatsonx, WatsonxEmbeddings

from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector

from langchain_core.messages import BaseMessage
from ibm_watsonx_ai import APIClient


class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    question: str
    documents: list[str]
    messages: Annotated[Sequence[BaseMessage], add_messages]


class GraphNodes:
    def __init__(self, api_client: APIClient, **kwargs: Any) -> None:
        self.api_client = api_client
        self.llm = ChatWatsonx(
            model_id=kwargs.get("model_id"), watsonx_client=api_client
        )
        self.graph = Neo4jGraph(url="bolt://localhost:7687", username="", password="")

        embedding_func = WatsonxEmbeddings(
            model_id=kwargs.get("embedding_model_id"), watsonx_client=api_client
        )

        self.vector_index = Neo4jVector.from_existing_index(
            graph=self.graph,
            embedding=embedding_func,
            index_name="vector",
            search_type="hybrid",
            node_label="Document",
            embedding_node_property="embedding",
            text_node_properties=["text"],
        )

    def _get_graph_qa_chain(self) -> GraphCypherQAChain:
        """Create a Neo4j Graph Cypher QA Chain"""
        # prompt = state["question"]

        graph_qa_chain = GraphCypherQAChain.from_llm(
            self.llm,
            graph=self.graph,
            verbose=True,
            top_k=5,
            allow_dangerous_requests=True,
        )
        return graph_qa_chain

    def graph_qa(self, state: AgentState) -> AgentState:
        """Returns a dictionary of at least one of the GraphState"""
        """ Invoke a Graph QA Chain """

        question = state["messages"][-1].content
        state["question"] = question

        graph_qa_chain = self._get_graph_qa_chain(state)

        result = graph_qa_chain.invoke(
            {
                # "context": graph.schema,
                "query": question,
            },
        )
        return {"documents": result, "question": question}
