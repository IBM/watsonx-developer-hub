from typing import Literal, TypedDict, Annotated, Sequence, TYPE_CHECKING

from ibm_watsonx_ai import APIClient  # type: ignore[import-untyped]
from langchain_ibm import ChatWatsonx
from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from langgraph_hitl.tools import web_search

if TYPE_CHECKING:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph.graph import CompiledGraph


def get_graph(
    client: APIClient, model_id: str, checkpointer: "InMemorySaver"
) -> "CompiledGraph":
    """Graph generator."""

    # Initialise ChatWatsonx
    chat = ChatWatsonx(
        model_id=model_id, watsonx_client=client, params={"temperature": 0.01}
    )

    # Define the shared graph state
    class State(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        decision: str

    # Agent node
    def agent(state: State) -> State:
        chat_with_tool = chat.bind_tools([web_search])
        response = chat_with_tool.invoke(state["messages"])
        return {**state, "messages": [response]}

    # Node for generating response when human approved
    def generate_response_approve(state: State) -> State:
        response = chat.invoke(state["messages"])
        return {**state, "messages": [response]}

    # Node for generating response when human rejected
    def generate_response_reject(state: State) -> State:
        # repeat answer generation without tool message
        response = chat.invoke(state["messages"][:-1])
        return {**state, "messages": [response]}

    # Human approval node
    def human_approval(
        state: State,
    ) -> Command[Literal["web_search", "generate_response_reject"]]:
        interruption_text = (
            "Do you approve the following output?\n\n"
            f"Tool Name: {str(state['messages'][-1].additional_kwargs.get('tool_calls')[0]['function'].get('name'))}\n"  # type: ignore[index]
            f"Tool argument: {str(state['messages'][-1].additional_kwargs.get('tool_calls')[0]['function'].get('arguments'))}\n\n"  # type: ignore[index]
            "If you approve the call respond with `approve`, and `reject` otherwise."
        )
        decision = interrupt({"interruption_text": interruption_text})

        if decision.lower() == "approve":
            print("✅ Approved path taken.")
            return Command(goto="web_search", update={"decision": "approved"})
        else:
            print("❌ Rejected path taken.")
            return Command(
                goto="generate_response_reject", update={"decision": "rejected"}
            )

    # Build the graph
    workflow = StateGraph(State)
    workflow.add_node("agent", agent)
    workflow.add_node("generate_response_approve", generate_response_approve)
    workflow.add_node("generate_response_reject", generate_response_reject)
    web_search_node = ToolNode([web_search])
    workflow.add_node("web_search", web_search_node)  # web search node
    workflow.add_node("human_approval", human_approval)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        lambda state: "use_tool"
        if bool(state["messages"][-1].additional_kwargs.get("tool_calls"))
        else "final",
        {
            "use_tool": "human_approval",  # If human approval needed
            # Otherwise we finish.
            "final": END,
        },
    )
    workflow.add_edge("web_search", "generate_response_approve")
    workflow.add_edge("generate_response_approve", END)
    workflow.add_edge("generate_response_reject", END)

    graph = workflow.compile(checkpointer=checkpointer)

    return graph
