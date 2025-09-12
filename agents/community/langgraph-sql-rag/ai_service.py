def deployable_ai_service(
    context,
    url,
    model_id,
    tool_config_connection_id,
    tool_config_schema,
    tool_config_dialect,
    tool_config_model_id,
    base_knowledge_description=None,
):
    import urllib
    from typing import Generator

    from langgraph_sql_rag.agent import get_graph_closure
    from ibm_watsonx_ai import APIClient, Credentials
    from langchain_core.messages import (
        BaseMessage,
        HumanMessage,
        AIMessage,
        SystemMessage,
        ToolMessage,
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

    graph = get_graph_closure(
        client,
        model_id,
        tool_config={
            "connection_id": tool_config_connection_id,
            "schema": tool_config_schema,
            "dialect": tool_config_dialect,
            "model_id": tool_config_model_id,
        }
    )()

    def _validate_messages(messages: list[dict]):
        if (
                messages
                and isinstance(messages, (list, tuple))
                and (messages[-1]["role"] == "user")
        ):
            return None
        raise ValueError(
            "The `messages` field must be an array containing objects, where the last one is representing user's message."
        )

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

        raw_messages = context.get_json()["messages"]
        _validate_messages(messages=raw_messages)

        messages = [convert_dict_to_message(_dict) for _dict in raw_messages]
        answer = graph.invoke({"messages": messages})
        last_message = answer["messages"][-1]
        # Retrieve query (only for benchmarking)
        import json

        sql_query_output = None
        for index, message in enumerate(answer["messages"][::-1], start=1):
            if isinstance(message, ToolMessage) and message.name == "sql_db_query":
                # Next message must contain tool_Call
                sql_query_output = json.loads(
                    answer["messages"][-index - 1].additional_kwargs["tool_calls"][0][
                        "function"
                    ]["arguments"]
                )["query"]
                break

        response = {
            "body": {
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": last_message.content,
                        },
                        # only for benchmarking
                        "final_sql_query": sql_query_output,
                    }
                ]
            }
        }
        return response

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

        client.set_token(context.get_token())

        payload = context.get_json()
        raw_messages = payload.get("messages", [])
        messages = [convert_dict_to_message(_dict) for _dict in raw_messages]

        response_stream = graph.stream(
            {"messages": messages}, stream_mode=["updates", "messages"]
        )

        _from_tool_evaluation = False
        last_update = None
        for chunk_type, data in response_stream:
            if chunk_type == "messages":
                if last_update is not None and last_update.get("agent", {}).get(
                        "messages", [AIMessage(content="")]
                )[0].additional_kwargs.get("tool_calls"):
                    _from_tool_evaluation = True
                if (delta := data[0].content) and not _from_tool_evaluation:
                    chunk_response = {
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant", "content": delta},
                            }
                        ]
                    }
                    yield chunk_response
            else:
                last_update = data
                _from_tool_evaluation = False

    return generate, generate_stream
