from typing import Callable, Annotated, Sequence

from typing_extensions import TypedDict
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from pydantic import BaseModel, Field
from typing import Literal

from langgraph.graph import END, StateGraph, START
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages

from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage

from langgraph_agentic_rag import retriever_tool_watsonx, sql_retriever_tool_watsonx, websearch_tool_watsonx


def get_graph_closure(
    client: APIClient,
    model_id: str,
    tool_config: dict,
    base_knowledge_description: str | None = None,
) -> Callable:
    """Graph generator closure."""

    # Initialise ChatWatsonx
    chat = ChatWatsonx(model_id=model_id, watsonx_client=client)
    chat_grader = ChatWatsonx(model_id=model_id, watsonx_client=client, disable_streaming = True)

    TOOLS = [
        retriever_tool_watsonx(
            api_client=client,
            tool_config=tool_config,
        ),
        sql_retriever_tool_watsonx(
            api_client=client,
        ),
        websearch_tool_watsonx(
            api_client=client,
            tool_config={"maxResults": 3},
        ),

    ]

    # Initialise memory saver
    # memory = MemorySaver()

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
            tools_used = []
            # query = messages[0]
            for m in reversed(messages):
                if hasattr(m, 'tool_call_id'):
                    print((f"I have tried tool: {m.name}"))
                    tools_used.append(m.name)
                if m.type == "human":
                    # query = m.content
                    query = m
                    break

            unused_tools = [t for t in TOOLS if t.name not in tools_used]
            if len(unused_tools) < 1:
                unused_tools = [websearch_tool_watsonx(api_client=client, tool_config={"maxResults": 3})]

            model = chat.bind_tools(unused_tools)
            print(f"unused tools: {[u.name for u in unused_tools]}")

            system_prompt = SystemMessage(
                default_system_prompt + "\n" + (instruction_prompt or "")
            )
            # response = model.invoke([system_prompt] + list(messages))
            response = model.invoke([query])
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
        # question = messages[-3].content
        for m in reversed(messages):
            if m.type == "human":
                question = m.content

        # Tool content
        last_message = messages[-1]
        docs = last_message.content

        # Prompt
        prompt = ChatPromptTemplate([
        ("user", "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If there is no context, just answer the question to be best of your knowledge. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.\nQuestion: {question} \nContext: {context} \nAnswer:")
        ])

        # Chain
        rag_chain = prompt | chat 

        # Run
        response = rag_chain.invoke({"context": docs, "question": question})
        return {"messages": [response]}
    

    # Edges
    def grade_documents(state) -> Literal["generate", "agent"]:
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (messages): The current state

        Returns:
            str: A decision for whether the documents are relevant or not
        """

        # logger.info("---CHECK RELEVANCE---")
        print("---CHECK RELEVANCE---")

        # Data model
        class grade(BaseModel):
            """Binary score for relevance check."""
            binary_score: str = Field(description="Relevance score 'yes' or 'no'")


        # LLM with tool and validation
        llm_with_tool = chat_grader.with_structured_output(grade)

        # Prompt
        prompt = PromptTemplate(
            template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
            Here is the retrieved document: \n\n {context} \n\n
            Here is the user question: {question} \n
            If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
            If the document mentions it has no data or no results to answer the question, or if the data is not directly available to answer the user question, it means the document is not relevant and grade it as 'no'. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
            input_variables=["context", "question"],
        )

        # Chain
        chain = prompt | llm_with_tool

        messages = state["messages"]
        last_message = messages[-1]

        # question = messages[0].content
        msg_cnt = 0
        for m in reversed(messages):
            if m.type == "human":
                question = m.content
                msg_cnt += 1
                break

        docs = last_message.content

        scored_result = chain.invoke({"question": question, "context": docs})

        score = scored_result.binary_score
        # for m in messages:
        #     print(m.type, "[messages]", m)
        if msg_cnt > 12:
            score = "yes"
            print("number of messages",len(messages))

        if score == "yes":
            print("---DECISION: DOCS RELEVANT---")
            return "generate"

        else:
            print("---DECISION: DOCS NOT RELEVANT---")
            return "agent"
    
    
    def rewrite(state):
        """
        Transform the query to produce a better question.

        Args:
            state (messages): The current state

        Returns:
            dict: The updated state with re-phrased question
        """

        # logger.info("---TRANSFORM QUERY---")
        print("---TRANSFORM QUERY---")
        messages = state["messages"]
        # question = messages[0].content
        for m in reversed(messages):
            if m.type == "human":
                question = m.content
                break
        

        msg = [
            HumanMessage(
                content=f""" \n 
        Look at the input and try to reason about the underlying semantic intent / meaning. \n 
        Here is the initial question:
        \n ------- \n
        {question} 
        \n ------- \n
        Formulate an improved question, output the question only: """,
            )
        ]
        response = chat.invoke(msg)
        print("rewrite message", response)
        return {"messages": [response]}

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
        # workflow.add_node("rewrite", rewrite)
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
                END: "generate",
            },
        )
        workflow.add_conditional_edges(
            "retrieve",
            # Assess agent decision
            grade_documents,
        )

        # Edges taken after the `action` node is called.
        # workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        # workflow.add_edge("rewrite", "agent")

        # Compile
        # graph = workflow.compile(checkpointer=memory)
        graph = workflow.compile()

        return graph

    return get_graph
