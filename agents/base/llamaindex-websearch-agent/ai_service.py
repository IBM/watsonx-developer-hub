def deployable_ai_service(context, url = None, space_id = None, model_id = None):
    import asyncio
    import nest_asyncio
    import threading
    import json
    from typing import Generator, AsyncGenerator
    from ibm_watsonx_ai import APIClient, Credentials
    from llama_index.core.base.llms.types import ChatMessage
    from llama_index_workflow_agent_base.agent import get_workflow_closure
    from llama_index_workflow_agent_base.workflow import (
        ToolCallEvent,
        StopEvent,
        InputEvent,
        StartEvent,
    )

    nest_asyncio.apply()  # We inject support for nested event loops

    persistent_loop = (
        asyncio.new_event_loop()
    )  # Create a persistent event loop that will be used by generate and generate_stream

    def start_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    threading.Thread(
        target=start_loop, args=(persistent_loop,), daemon=True
    ).start()  # We run a persistent loop in a separate daemon thread

    def get_formatted_message(resp: ChatMessage) -> dict | None:
        role = resp.role
        if resp.blocks:
            if role == "assistant":
                return {"role": "assistant", "content": resp.blocks[0].text}
            elif role == "tool":
                tool_call_id = resp.additional_kwargs["tool_call_id"]
                return {
                    "role": "tool",
                    "id": f"fake_id_{tool_call_id}",
                    "tool_call_id": tool_call_id,
                    "name": resp.additional_kwargs["name"],
                    "content": resp.blocks[0].text,
                }
        elif role == "assistant":
            if additional_kw := resp.additional_kwargs:
                tool_call = additional_kw["tool_calls"][0]
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

    def get_formatted_message_stream(
        resp: ChatMessage, is_assistant: bool = False
    ) -> list | None:

        if isinstance(resp, StartEvent):

            return

        elif isinstance(resp, InputEvent):

            responses = []

            resp_input = resp.input

            last_assistant_index = None

            for index, message in enumerate(resp_input):
                if message.role == "assistant":
                    last_assistant_index = index

            if last_assistant_index is not None:
                for event_input in resp_input[last_assistant_index + 1 :]:

                    if event_input.role == "tool":

                        tool_call_id = event_input.additional_kwargs["tool_call_id"]
                        if is_assistant:
                            to_queue = {
                                "role": "assistant",
                                "step_details": {
                                    "type": "tool_response",
                                    "id": f"tool_call_id_{tool_call_id}",
                                    "tool_call_id": tool_call_id,
                                    "name": event_input.additional_kwargs["name"],
                                    "content": event_input.blocks[0].text,
                                },
                            }
                        else:
                            to_queue = {
                                "role": "tool",
                                "id": f"tool_call_id_{tool_call_id}",
                                "tool_call_id": tool_call_id,
                                "name": event_input.additional_kwargs["name"],
                                "content": event_input.blocks[0].text,
                            }

                        responses.append(to_queue)

            return responses

        elif isinstance(resp, ToolCallEvent):
            # Tool calls
            responses = []

            for tool_call in resp.tool_calls:

                arguments_str = json.dumps(tool_call.tool_kwargs)

                if is_assistant:
                    to_queue = {
                        "role": "assistant",
                        "step_details": {
                            "type": "tool_calls",
                            "tool_calls": [
                                {
                                    "id": tool_call.tool_id,
                                    "name": tool_call.tool_name,
                                    "args": arguments_str,
                                }
                            ],
                        },
                    }
                else:
                    to_queue = {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call.tool_id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.tool_name,
                                    "arguments": arguments_str,
                                },
                            }
                        ],
                    }

                responses.append(to_queue)

            return responses

        elif isinstance(resp, StopEvent):
            # Final response
            resp_result = resp.result
            resp_response = resp_result["response"]
            to_queue = {
                "role": "assistant",
                "content": resp_response.message.blocks[0].text,
            }

            return [to_queue]

    async def generate_async(context) -> dict:
        """
        The `generate` function handles the REST call to the inference endpoint
        POST /ml/v4/deployments/{id_or_name}/ai_service

        The generate function should return a dict
        The following optional keys are supported currently
        - data

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
        client = APIClient(
            credentials=Credentials(url=url, token=context.get_token()),
            space_id=space_id,
        )
        workflow = get_workflow_closure(client, model_id)

        payload = context.get_json()
        messages = payload.get("messages", [])

        if messages and messages[0]["role"] == "system":
            agent = workflow(messages[0]["content"])
            del messages[0]
        else:
            agent = workflow()

        return await agent.run(input=messages)

    async def generate_async_stream(context) -> AsyncGenerator:
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
        client = APIClient(
            credentials=Credentials(url=url, token=context.get_token()),
            space_id=space_id,
        )
        workflow = get_workflow_closure(client, model_id)

        payload = context.get_json()
        headers = context.get_headers()
        is_assistant = headers.get("X-Ai-Interface") == "assistant"

        messages = payload.get("messages", [])

        if messages and messages[0]["role"] == "system":
            agent = workflow(messages[0]["content"])
            del messages[0]
        else:
            agent = workflow()

        handler = agent.run(input=messages)

        async for ev in handler.stream_events():
            if (messages := get_formatted_message_stream(ev, is_assistant)) is not None:
                for message in messages:
                    if isinstance(ev, ToolCallEvent):
                        yield {
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": message,
                                    "finish_reason": "tool_calls",
                                }
                            ]
                        }
                    elif isinstance(ev, StopEvent):
                        finish_reason = (
                            ev.result["response"]
                            .raw.get("choices")[0]
                            .get("finish_reason")
                        )
                        yield {
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": message,
                                    "finish_reason": finish_reason,
                                }
                            ]
                        }
                    else:
                        # Tool call result
                        yield {"choices": [{"index": 0, "delta": message}]}

        await handler

    def generate(context) -> dict:
        """
        A synchronous wrapper for the asynchronous `generate_async` method.
        """

        future = asyncio.run_coroutine_threadsafe(
            generate_async(context), persistent_loop
        )
        generated_response = future.result()
        message = get_formatted_message(generated_response["messages"][-1])
        choices = [{"index": 0, "message": message}]

        return {
            "headers": {"Content-Type": "application/json"},
            "body": {"choices": choices},
        }

    def generate_stream(context) -> Generator:
        """
        A synchronous wrapper for the asynchronous `generate_async_stream` method.
        """

        gen = generate_async_stream(context)

        while True:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    gen.__anext__(), persistent_loop
                )
                value = future.result()
            except StopAsyncIteration:
                break
            yield value

    return generate, generate_stream
