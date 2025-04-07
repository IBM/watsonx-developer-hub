def deployable_ai_service(context, url=None, space_id=None, model_id=None):
    import asyncio
    import nest_asyncio
    import threading
    from typing import Generator, AsyncGenerator
    from ibm_watsonx_ai import Credentials
    from autogen_core import CancellationToken
    from autogen_agent_base.agent import get_agent_chat
    from autogen_agentchat.messages import (
        TextMessage,
        BaseChatMessage,
        BaseAgentEvent,
        BaseMessage,
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

    def get_choice_from_message(message: BaseMessage) -> dict:
        choice = {
            "index": 0,
            "delta": {
                "role": message.source,
                "content": message.content,
            },
            "finish_reason": "tool_calls",
        }

        if message.source == "user":
            choice["finish_reason"] = "user"
            return choice

        if message.type == "ToolCallSummaryMessage":
            choice["delta"]["role"] = "tool"
            choice["delta"]["finish_reason"] = "tool_calls"
        elif message.type == "ToolCallRequestEvent":
            tool_calls = []
            for function_call in message.content:
                tool = {
                    "id": function_call.id,
                    "name": function_call.name,
                    "args": function_call.arguments,
                }
                tool_calls.append(tool)
            choice["delta"] = {
                "role": message.source,
                "type": "tool_calls",
                "tool_calls": tool_calls,
            }

        elif message.type == "ToolCallExecutionEvent":
            tool_calls = []
            for function_call in message.content:
                tool = {
                    "content": function_call.content,
                    "tool_call_id": function_call.call_id,
                    "name": function_call.name,
                    "is_error": function_call.is_error,
                }
                tool_calls.append(tool)
            choice["delta"] = {
                "role": message.source,
                "type": "tool_calls",
                "tool_calls": tool_calls,
            }

        return choice

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

        credentials = Credentials(url=url, token=context.get_token())

        agent = get_agent_chat(credentials, model_id, space_id)

        payload = context.get_json()
        messages = payload.get("messages", [])

        text_messages = [
            TextMessage(content=message.get("content"), source=message.get("role"))
            for message in messages
        ]

        return await agent().run(
            task=text_messages,
            cancellation_token=CancellationToken(),
        )

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
        credentials = Credentials(url=url, token=context.get_token())

        agent = get_agent_chat(credentials, model_id, space_id)

        payload = context.get_json()
        messages = payload.get("messages", [])

        text_messages = [
            TextMessage(content=message.get("content"), source=message.get("role"))
            for message in messages
        ]
        was_chunk = False
        async for message in agent().run_stream(task=text_messages):
            if getattr(message, "type", None) is None:  # e.g TaskResult
                break

            delta = {"role": message.source, "content": message.content}
            choice = {"index": 0, "delta": delta}

            if isinstance(message, BaseAgentEvent):
                if message.type == "ModelClientStreamingChunkEvent":
                    was_chunk = True
                else:
                    choice = get_choice_from_message(message)

            elif isinstance(message, BaseChatMessage):
                choice = get_choice_from_message(message)

                if was_chunk:
                    break

            yield {"choices": [choice]}

    def generate(context) -> dict:
        """
        A synchronous wrapper for the asynchronous `generate_async` method.
        """

        future = asyncio.run_coroutine_threadsafe(
            generate_async(context), persistent_loop
        )
        generated_response = future.result()
        choices = [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": generated_response.messages[-1].content,
                },
            }
        ]
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
