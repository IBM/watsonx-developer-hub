from typing import Annotated, Sequence, Any

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

from langchain_ibm import ChatWatsonx, WatsonxEmbeddings

from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from ibm_watsonx_ai import APIClient

from pydantic import BaseModel, Field


class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    question: str
    documents: list[str]
    messages: Annotated[Sequence[BaseMessage], add_messages]


class Entities(BaseModel):
    """List of identified entities."""

    names: list[str] = Field(
        ...,
        description="Distinct, individual elements (entities), including people, organizations, or companies that appear in the text.",
    )


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

    def _retrieve_entities(self, question: str) -> list[str]:
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant who specializes "
                        "in extracting entities such as people, organizations, or companies from user text. "
                    ),
                },
                {
                    "role": "user",
                    "content": "Use a given format to extract information from the user input: {question}",
                },
            ]
        )

        entity_chain = chat_prompt | self.llm.with_structured_output(Entities)

        return entity_chain.invoke({"question": question}).names
    
    def graph_search(self, state: AgentState) -> AgentState:
        question = state["question"]

        entities = self._retrieve_entities(question)

        for entity in entities:
            self.graph.query(
            """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
            YIELD node,score
            CALL {
              WITH node
              MATCH (node)-[r:!MENTIONS]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
              UNION ALL
              WITH node
              MATCH (node)<-[r:!MENTIONS]-(neighbor)
              RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            }
            RETURN output LIMIT 50
            """,
            {"query": generate_full_text_query(entity)},
        )

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
