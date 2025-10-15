def deployable_ai_service(context, url=None, model_id=None):
    import urllib
    from typing import Generator
    import uuid

    from langgraph_hitl.agent import get_graph
    from ibm_watsonx_ai import APIClient, Credentials
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
    )

    from langgraph.types import Command
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()

    hostname = urllib.parse.urlparse(url).hostname or ""
    is_cloud_url = hostname.lower().endswith("cloud.ibm.com")
    instance_id = None if is_cloud_url else "openshift"

    client = APIClient(
        credentials=Credentials(
            url=url,
            token=context.generate_token(),
            instance_id=instance_id,
        ),
        space_id=context.get_space_id(),
    )

    graph = get_graph(client, model_id, checkpointer)

    default_system_prompt = (
        "You are a helpful AI assistant, "
        "please respond to the user's query to the best of your ability!"
    )

    def get_formatted_message(
        resp: BaseMessage, is_assistant: bool = False
    ) -> dict | None:
        role = resp.type

        if resp.content:
            if role in {"AIMessageChunk", "ai"}:
                return {"role": "assistant", "content": resp.content}
            elif role == "tool":
                if is_assistant:
                    return {
                        "role": "assistant",
                        "step_details": {
                            "type": "tool_response",
                            "id": resp.id,
                            "tool_call_id": resp.tool_call_id,
                            "name": resp.name,
                            "content": resp.content,
                        },
                    }
                else:
                    return {
                        "role": role,
                        "id": resp.id,
                        "tool_call_id": resp.tool_call_id,
                        "name": resp.name,
                        "content": resp.content,
                    }
        elif role == "ai":  # this implies resp.additional_kwargs
            if additional_kw := resp.additional_kwargs:
                tool_call = additional_kw["tool_calls"][0]
                if is_assistant:
                    return {
                        "role": "assistant",
                        "step_details": {
                            "type": "tool_calls",
                            "tool_calls": [
                                {
                                    "id": tool_call["id"],
                                    "name": tool_call["function"]["name"],
                                    "args": tool_call["function"]["arguments"],
                                }
                            ],
                        },
                    }
                else:
                    return {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call["id"],
                                "type": "function",
                                "function": {
                                    "name": tool_call["function"]["name"],
                                    "arguments": tool_call["function"]["arguments"],
                                },
                            }
                        ],
                    }

    def convert_dict_to_message(_dict: dict) -> BaseMessage:
        """Convert user message in dict to langchain_core.messages.BaseMessage"""

        if _dict["role"] == "assistant":
            return AIMessage(content=_dict["content"])
        elif _dict["role"] == "system":
            return SystemMessage(content=_dict["content"])
        else:
            return HumanMessage(content=_dict["content"])

    def generate(context) -> dict:
        """
        The `generate` function handles the REST call to the inference endpoint
        POST /ml/v4/deployments/{id_or_name}/ai_service

        The generate function should return a dict

        A JSON body sent to the above endpoint should follow the format:
        {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that uses tools to answer questions in detail.",
                },
                {
                    "role": "user",
                    "content": "Hello!",
                },
            ]
        }
        Please note that the `system message` MUST be placed first in the list of messages!
        """

        # Overwrite inner context token in the API client
        client.set_token(context.get_token())
        payload = context.get_json()
        raw_messages = payload.get("messages", [])
        messages = [convert_dict_to_message(_dict) for _dict in raw_messages]

        if messages and messages[0].type != "system":
            messages = [SystemMessage(content=default_system_prompt)] + messages

        thread_id = payload.get("thread_id")

        # Check if this is approve/reject requests
        if thread_id is not None:
            config = {"configurable": {"thread_id": thread_id}}
            generated_response = graph.invoke(
                Command(resume=messages[-1].content), config=config
            )

        else:
            # Otherwise, create a new thread id that will be removed:
            # - at the end of generation, when no human approval needed
            # - after the user will send back the approval when human interference needed

            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            generated_response = list(
                graph.stream({"messages": messages}, config=config)
            )[-1]

        choices = []
        execute_response = {
            "headers": {"Content-Type": "application/json"},
            "body": {"choices": choices},
        }
        if (interrupt_info := generated_response.get("__interrupt__")) is not None:
            execute_response["body"]["thread_id"] = config["configurable"]["thread_id"]
            message = get_formatted_message(
                AIMessage(content=interrupt_info[0].value["interruption_text"])
            )
        else:
            message = get_formatted_message(
                generated_response.get("agent", generated_response)["messages"][-1]
            )
            # remove thread_id from checkpointer memory
            checkpointer.delete_thread(thread_id)

        choices.append(
            {
                "index": 0,
                "message": message,
            }
        )

        return execute_response

    def generate_stream(context) -> Generator[dict, None, None]:
        """
        The `generate_stream` function handles the REST call to the Server-Sent Events (SSE) inference endpoint
        POST /ml/v4/deployments/{id_or_name}/ai_service_stream

        The generate function should return a dict

        A JSON body sent to the above endpoint should follow the format:
        {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that uses tools to answer questions in detail.",
                },
                {
                    "role": "user",
                    "content": "Hello!",
                },
            ]
        }
        Please note that the `system message` MUST be placed first in the list of messages!
        """
        headers = context.get_headers()
        is_assistant = headers.get("X-Ai-Interface") == "assistant"

        # Overwrite inner context token in the API client
        client.set_token(context.get_token())
        payload = context.get_json()
        raw_messages = payload.get("messages", [])
        thread_id = payload.get("thread_id")
        messages = [convert_dict_to_message(_dict) for _dict in raw_messages]

        if messages and messages[0].type != "system":
            messages = [SystemMessage(content=default_system_prompt)] + messages

        # Check if this is approve/reject requests
        if thread_id is not None:
            config = {"configurable": {"thread_id": thread_id}}
            response_stream = graph.stream(
                Command(resume=messages[-1].content),
                config=config,
                stream_mode=["updates", "messages"],
            )

        else:
            # Otherwise, create a new thread id that will be removed:
            # - at the end of generation, when no human approval needed
            # - after the user will send back the approval when human interference needed

            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            response_stream = graph.stream(
                {"messages": messages},
                config=config,
                stream_mode=["updates", "messages"],
            )

        thread_id = None
        for chunk_type, data in response_stream:
            if chunk_type == "messages":
                msg_obj = data[0]
            elif chunk_type == "updates":
                if agent := data.get("agent"):
                    msg_obj = agent["messages"][0]
                    checkpointer.delete_thread(thread_id)
                    if msg_obj.response_metadata.get("finish_reason") == "stop":
                        continue
                elif tool := data.get("tools"):
                    msg_obj = tool["messages"][0]

                # interrupt node
                elif (interrupt_info := data.get("__interrupt__")) is not None:
                    thread_id = config["configurable"]["thread_id"]
                    msg_obj = AIMessage(
                        content=interrupt_info[0].value["interruption_text"]
                    )
                else:
                    continue
            else:
                continue

            if (
                message := get_formatted_message(msg_obj, is_assistant=is_assistant)
            ) is not None:
                chunk_response = {
                    "choices": [
                        {
                            "index": 0,
                            "delta": message,
                            "finish_reason": msg_obj.response_metadata.get(
                                "finish_reason"
                            ),
                        }
                    ],
                }
                if thread_id is not None:
                    chunk_response["thread_id"] = thread_id
                yield chunk_response

    return generate, generate_stream
