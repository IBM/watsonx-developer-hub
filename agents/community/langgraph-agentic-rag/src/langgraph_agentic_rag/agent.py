from typing import Callable, Annotated, Sequence

from typing_extensions import TypedDict

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx

from langgraph.graph import END, StateGraph, START
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages

from langgraph.prebuilt import ToolNode, tools_condition

from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage

from langgraph_agentic_rag import retriever_tool_watsonx


def get_graph_closure(
    client: APIClient,
    model_id: str,
    tool_config: dict,
    base_knowledge_description: str | None = None,
) -> Callable:
    """Graph generator closure."""

    # Initialise ChatWatsonx
    chat = ChatWatsonx(model_id=model_id, watsonx_client=client)

    TOOLS = [
        retriever_tool_watsonx(
            api_client=client,
            tool_config=tool_config,
        )
    ]

    # Define system prompt
    default_system_prompt = (
        f"You are a helpful AI assistant, please respond to the user's query to the best of your ability!"
        "\n\n"
        f"Vector Store Index knowledge description: {base_knowledge_description or ''}"
    )

    class AgentState(TypedDict):
        # The add_messages function defines how an update should be processed
        # Default is to replace. add_messages says "append"
        messages: Annotated[Sequence[BaseMessage], add_messages]

    ### Nodes

    def agent_with_instruction(instruction_prompt: str | None) -> Callable:
        """System prompt will be updated by instruction prompt."""

        def agent(state: AgentState) -> dict:
            """
            Invokes the agent model to generate a response based on the current state. Given
            the question, it will decide to retrieve using the retriever tool, or simply end.

            Args:
                state (messages): The current state

            Returns:
                dict: The updated state with the agent response appended to messages
            """
            messages = state["messages"]

            model = chat.bind_tools(TOOLS)
            system_prompt = SystemMessage(
                default_system_prompt + "\n" + (instruction_prompt or "")
            )
            response = model.invoke([system_prompt] + list(messages))
            # We return a list, because this will get added to the existing list
            return {"messages": [response]}

        return agent

    def generate(state: AgentState):
        """
        Generate answer

        Args:
            state (messages): The current state

        Returns:
            dict: The updated state with re-phrased question
        """
        messages = state["messages"]

        # Most recent user query
        question = messages[-3].content

        # Tool content
        last_message = messages[-1]
        docs = last_message.content

        # Prompt
        prompt = hub.pull("rlm/rag-prompt")

        # Chain
        rag_chain = prompt | chat | StrOutputParser()

        # Run
        response = rag_chain.invoke({"context": docs, "question": question})
        return {"messages": [AIMessage(response)]}

    def get_graph(instruction_prompt: SystemMessage | None = None) -> CompiledGraph:
        """Get compiled graph with overwritten system prompt, if provided"""

        # Define a new graph
        workflow = StateGraph(AgentState)

        if instruction_prompt is None:
            agent = agent_with_instruction(instruction_prompt)
        else:
            agent = agent_with_instruction(instruction_prompt.content)

        # Define the nodes
        workflow.add_node("agent", agent)  # agent
        retrieve = ToolNode(TOOLS)
        workflow.add_node("retrieve", retrieve)  # retrieval
        workflow.add_node("generate", generate)  # generate answer

        # Call agent node to decide to retrieve or not
        workflow.add_edge(START, "agent")

        # Decide whether to retrieve
        workflow.add_conditional_edges(
            "agent",
            # Assess agent decision
            tools_condition,
            {
                # Translate the condition outputs to nodes in our graph
                "tools": "retrieve",
                END: END,
            },
        )

        # Edges taken after the `action` node is called.
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        # Compile
        graph = workflow.compile()

        return graph

    return get_graph
