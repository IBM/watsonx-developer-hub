from typing import Annotated, Sequence, List, Literal

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

from langchain_ibm import ChatWatsonx, WatsonxEmbeddings

from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_neo4j.vectorstores.neo4j_vector import remove_lucene_chars

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from ibm_watsonx_ai import APIClient

from pydantic import BaseModel, Field

from ibm_cloud_sdk_core.authenticators import BearerTokenAuthenticator
from ibm_secrets_manager_sdk.secrets_manager_v2 import SecretsManagerV2


class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
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
    def __init__(
        self,
        api_client: APIClient,
        system_message: SystemMessage,
        model_id: str,
        embedding_model_id: str,
        service_manager_service_url: str,
        secret_id: str,
    ) -> None:
        self.api_client = api_client
        self.llm = ChatWatsonx(model_id=model_id, watsonx_client=api_client)
        self.llm_no_stream = ChatWatsonx(
            model_id=model_id, watsonx_client=api_client, streaming=False
        )

        embedding_func = WatsonxEmbeddings(
            model_id=embedding_model_id, watsonx_client=api_client
        )

        # Neo4j
        # authenticator = BearerTokenAuthenticator(api_client.token)
        # secretsManager = SecretsManagerV2(authenticator=authenticator)
        # secretsManager.set_service_url(service_url=service_manager_service_url)
        # response = secretsManager.get_secret(id=secret_id)

        # self.graph = Neo4jGraph(
        #     url=response.result["data"]["neo4j_uri"],
        #     username=response.result["data"]["neo4j_username"],
        #     password=response.result["data"]["neo4j_password"],
        #     database=response.result["data"]["neo4j_database"],
        # )
        self.graph = None

        self.vector_index = None
        # self.vector_index = Neo4jVector.from_existing_index(
        #     graph=self.graph,
        #     embedding=embedding_func,
        #     index_name="vector",
        #     keyword_index_name="keyword",
        #     search_type="hybrid",
        #     node_label="Document",
        #     embedding_node_property="embedding",
        # )

        self.system_message = system_message

    def agent(self, state: AgentState) -> dict:
        """
        Invokes the agent model to generate a response based on the current state. Given
        the question, it will decide to retrieve using the retriever tool, or simply end.

        Args:
            state (AgentState): The current Agent state

        Returns:
            dict: The updated state with the route
        """

        class Router(BaseModel):
            route: Literal["graph_knowledge_base", "final_answer"] = Field(
                description=(
                    "Literal type that can only take two values 'graph_knowledge_base' or 'final_answer'. "
                    "This field determines the path or the specific operation that the router will handle."
                )
            )

        # Adding knowledge base description will increase the quality of model response
        system_message = SystemMessage(
            content=(
                "You are helpful assistant who specializes in routing the workflow. "
                "If you need to retrieve information from a knowledge base to answer user query, please respond with 'graph_knowledge_base'. "
                "Otherwise, respond with 'final_answer'."
            )
        )
        human_message = HumanMessage(
            content=f"User query: {state['messages'][-1].content}"
        )
        llm_with_tool = self.llm_no_stream.bind_tools([Router], tool_choice="Router")
        response = llm_with_tool.invoke([system_message, human_message])
        response.response_metadata["finish_reason"] = "tool_calls"

        return {"messages": [response]}

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

    def graph_search(self, state: AgentState) -> dict:
        """Graph traversal node.

        Args:
            state (AgentState): The current Agent state

        Returns:
            dict: The updated Agent state with updated structured data
        """
        question = state["messages"][-1].content
        entities = self._retrieve_entities(question)

        result = ""
        for entity in entities:
            response = [{"output": "Marie Curie - ORIGIN -> Poland"}]
            # response = self.graph.query(
            #     """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
            # YIELD node,score
            # CALL () {
            #   MATCH (node)-[r:!MENTIONS]->(neighbor)
            #   RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
            #   UNION
            #   MATCH (node)<-[r:!MENTIONS]-(neighbor)
            #   RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            # }
            # RETURN output LIMIT 20
            # """,
            #     {"query": self._generate_full_text_query(entity)},
            # )
            result += "\n".join([el["output"] for el in response])

        return {
            "structured_data": result,
            # "messages": [
            #     ToolMessage(
            #         content=result,
            #         name="graph_search",
            #         tool_call_id="chat_graph_search_tool_id",
            #     )
            # ],
        }

    def unstructured_retriever(self, state: AgentState) -> dict:
        """Vector retriever node.

        Args:
            state (AgentState): The current Agent state

        Returns:
            dict: The updated Agent state with updated unstructured_data
        """
        question = state["messages"][-2].content
        unstructured_data = [
            "Marie Curie, born in 1867, was a Polish and naturalised-French physicist and chemist who conducted pioneering research on radioactivity."
        ]

        return {
            "unstructured_data": unstructured_data,
            "messages": [
                ToolMessage(
                    content="\n".join(
                        map(
                            lambda doc: "#Document:\n" + doc + "\n",
                            unstructured_data,
                        )
                    ),
                    name="Router",
                    tool_call_id="vector_retriever_tool_id",
                )
            ],
        }

    def generate(self, state: AgentState) -> dict:
        """Generate node.

        Args:
            state (AgentState): The current Agent state

        Returns:
            dict: The updated state with final AI assistant response
        """
        if state.get("structured_data"):
            # template with data
            final_data = f"""Structured data:
{state["structured_data"]}
Unstructured data:
{"#Document ".join(state["unstructured_data"])}
            """
            user_prompt = f"""Answer the question based only on the following context:
{final_data}

Question: {state["messages"][-3].content}
    """
        else:
            user_prompt = state["messages"][-1].content
        response = self.llm.invoke(
            [
                self.system_message,
                *state["messages"][:-1],
                HumanMessage(content=user_prompt),
            ]
        )
        return {"messages": [response]}
