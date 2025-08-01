def deployable_ai_service(context, url=None, model_id=None, postgres_db_connection_id=None):
    import urllib
    from typing import Generator
    from langgraph.checkpoint.postgres import PostgresSaver
    from langgraph_react_with_database_memory.agent import get_graph_closure
    from ibm_watsonx_ai import APIClient, Credentials
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
    )

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

    def generate_database_URI():
        db_details = client.connections.get_details(postgres_db_connection_id)
        db_credentials = db_details["entity"]["properties"]
        db_host = db_credentials["host"]
        db_port = db_credentials["port"]
        db_name = db_credentials["database"] 
        db_username = db_credentials["username"]
        db_password = db_credentials["password"]
        return f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    DB_URI = generate_database_URI()

    graph = get_graph_closure(client, model_id)

    with PostgresSaver.from_conn_string(DB_URI) as saver:
        saver.setup()

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

        client.set_token(context.get_token())
        payload = context.get_json()
        raw_messages = payload.get("messages", [])
        thread_id = payload.get("thread_id")
        messages = [convert_dict_to_message(_dict) for _dict in raw_messages]
        with PostgresSaver.from_conn_string(DB_URI) as saver:
            if messages and messages[0].type == "system":
                agent = graph(saver, thread_id, messages[0].content)
                del messages[0]
            else:
                agent = graph(saver, thread_id)
            
            if thread_id:
                config = {"configurable": {"thread_id": thread_id}}
                generated_response = agent.invoke({"messages": messages}, config)
            else:
                generated_response = agent.invoke({"messages": messages})

            choices = []
            execute_response = {
                "headers": {"Content-Type": "application/json"},
                "body": {"choices": choices},
            }

            choices.append(
                {
                    "index": 0,
                    "message": get_formatted_message(generated_response["messages"][-1]),
                }
            )

            return execute_response
    
    def generate_stream(context) -> Generator[dict, ..., ...]:
        """
        The `generate_stream` function handles the REST call to the Server-Sent Events (SSE) inference endpoint
        POST /ml/v4/deployments/{id_or_name}/ai_service_stream

        The generate function should return a dict

        A JSON body sent to the above endpoint should follow the format:
        {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that uses tools to answer questions in detail."
                },
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
        }
        Please note that the `system message` MUST be placed first in the list of messages!
        """
        headers = context.get_headers()
        is_assistant = headers.get("X-Ai-Interface") == "assistant"

        client.set_token(context.get_token())
        payload = context.get_json()
        raw_messages = payload.get("messages", [])
        thread_id = payload.get("thread_id")
        messages = [convert_dict_to_message(_dict) for _dict in raw_messages]
        with PostgresSaver.from_conn_string(DB_URI) as saver:
            if messages and messages[0].type == "system":
                agent = graph(saver, thread_id, messages[0].content)
                del messages[0]
            else:
                agent = graph(saver, thread_id)
            
            if thread_id:
                config = {"configurable": {"thread_id": thread_id}}
                response_stream = agent.stream(
                    {"messages": messages}, config, stream_mode=["updates", "messages"]
                )
            else:
                response_stream = agent.stream(
                    {"messages": messages}, stream_mode=["updates", "messages"]
                )

            for chunk_type, data in response_stream:
                if chunk_type == "messages":
                    msg_obj = data[0]
                    if msg_obj.type == "tool":
                        continue
                elif chunk_type == "updates":
                    if agent := data.get("agent"):
                        msg_obj = agent["messages"][0]
                        if msg_obj.response_metadata.get("finish_reason") == "stop":
                            continue
                    elif tool := data.get("tools"):
                        msg_obj = tool["messages"][0]
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
                        ]
                    }
                    yield chunk_response

    return generate, generate_stream
