from typing import Callable

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import (
        BaseMessage,
        AIMessage,
        HumanMessage,
        SystemMessage,
        ToolMessage,
)
from langgraph_sql_rag import sql_tools_watsonx


def get_graph_closure(client: APIClient, model_id: str, tool_config: dict) -> Callable:
    """Graph generator closure."""

    # Initialise ChatWatsonx
    chat = ChatWatsonx(model_id=model_id, watsonx_client=client, params={"temperature": 0.01})

    # Define system prompt
    SYSTEM_PROMPT_TEMPLATE = """You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
    Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.
    You have access to tools for interacting with the database.
    Only use the below tools. Only use the information returned by the below tools to construct your final answer.
    You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

    To start you should ALWAYS look at the tables in the database to see what you can query.
    Do NOT skip this step.
    Then you should query the schema of the most relevant tables."""

    system_prompt_template = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT_TEMPLATE)]
    )
    default_system_prompt = system_prompt_template.format(dialect=tool_config['dialect'], top_k=3)

    tools = sql_tools_watsonx(
        api_client=client,
        tool_config=tool_config,
    )


    def get_graph(system_prompt=default_system_prompt) -> CompiledGraph:
        """Get compiled graph with overwritten db dialect, if provided"""

        # Create instance of compiled graph
        return create_react_agent(
            chat, tools=tools, state_modifier=system_prompt
        )

    return get_graph
