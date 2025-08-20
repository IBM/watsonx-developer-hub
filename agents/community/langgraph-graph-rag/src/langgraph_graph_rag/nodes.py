from typing import Annotated, Sequence, Any, List

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

from langchain_ibm import ChatWatsonx, WatsonxEmbeddings

from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector
from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from ibm_watsonx_ai import APIClient

from pydantic import BaseModel, Field


class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    question: str
    structured_data: str
    unstructured_data: List[str]
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Extract entities from text
class Entities(BaseModel):
    """Identifying information about entities."""

    names: List[str] = Field(
        ...,
        description="All the person, organization, or business entities that "
        "appear in the text.",
    )


class GraphNodes:
    def __init__(self, api_client: APIClient, **kwargs: Any) -> None:
        self.api_client = api_client
        self.llm = ChatWatsonx(
            model_id=kwargs.get("model_id"), watsonx_client=api_client
        )
        self.graph = Neo4jGraph(
            url="bolt://localhost:7687", username="neo4j", password="password"
        )

        embedding_func = WatsonxEmbeddings(
            model_id=kwargs.get("embedding_model_id"), watsonx_client=api_client
        )

        self.vector_index = Neo4jVector.from_existing_index(
            graph=self.graph,
            embedding=embedding_func,
            index_name="vector",
            keyword_index_name="keyword",
            search_type="hybrid",
            node_label="Document",
            embedding_node_property="embedding",
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

    def _generate_full_text_query(self, input_text: str) -> str:
        """
        Generate a full-text search query for a given input string.

        This function constructs a query string suitable for a full-text search.
        It processes the input string by splitting it into words and appending a
        similarity threshold (~2 changed characters) to each word, then combines
        them using the AND operator. Useful for mapping entities from user questions
        to database values, and allows for some misspelings.
        """
        full_text_query = ""
        words = remove_lucene_chars(input_text).split()
        for word in words[:-1]:
            full_text_query += f" {word}~2 AND"
        full_text_query += f" {words[-1]}~2"
        return full_text_query.strip()

    def graph_search(self, question: str) -> AgentState:
        entities = self._retrieve_entities(question)

        for entity in entities:
            response = self.graph.query(
                """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
                YIELD node,score
                CALL {
                MATCH (node)-[r:!MENTIONS]->(neighbor)
                RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
                UNION
                MATCH (node)<-[r:!MENTIONS]-(neighbor)
                RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
                }
                RETURN output LIMIT 50
                """,
                {"query": self._generate_full_text_query(entity)},
            )
            result += "n".join([str(el) for el in response])
        return result

    def retriever(self, state: AgentState) -> AgentState:
        question = state["messages"][-1].content
        structured_data = self.graph_search(question)
        unstructured_data = [
            el.page_content for el in self.vector_index.similarity_search(question)
        ]

        return {
            "structured_data": structured_data,
            "unstructured_data": unstructured_data,
            "question": question,
        }

    def generate(self, state: AgentState) -> AgentState:
        final_data = f"""Structured data:
    {state["structured_data"]}
    Unstructured data:
    {"#Document ".join(state["unstructured_data"])}
        """
        user_prompt = (
            f"""Answer the question based only on the following context:
{final_data}

Question: {state["question"]}
""",
        )
        system_prompt = "You are helpful assistant"
        response = self.llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        return {"messages": [response]}
