def deployable_ai_service(context, **custom):
    import asyncio
    import nest_asyncio
    import threading
    from typing import Generator, AsyncGenerator
    from ibm_watsonx_ai import Credentials
    from autogen_core import CancellationToken
    from autogen_agentchat.ui import Console
    from autogen_agent_base.agent import get_workflow_closure
    from autogen_agentchat.messages import TextMessage
    from autogen_agentchat.base import TaskResult
    from autogen_watsonx_client.client import _autogen_message_to_watsonx_message

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
        model_id = custom.get("model_id")

        credentials = Credentials(url=custom.get("url"), token=context.get_token())

        agent = get_workflow_closure(
            credentials, model_id, custom.get("project_id"), custom.get("space_id")
        )

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
        model_id = custom.get("model_id")
        credentials = Credentials(url=custom.get("url"), token=context.get_token())

        agent = get_workflow_closure(
            credentials, model_id, custom.get("project_id"), custom.get("space_id")
        )

        payload = context.get_json()
        messages = payload.get("messages", [])

        text_messages = [
            TextMessage(content=message.get("content"), source=message.get("role"))
            for message in messages
        ]

        async for message in agent().run_stream(task=text_messages):
            if isinstance(message, TaskResult):
                # print("Stop Reason:", message)
                break
            else:
                delta = {
                    "role": message.source,
                    "content": message.content,
                }
                yield {
                    "choices": [
                        {
                            "index": 0,
                            "delta": delta,
                            "finish_reason": "tool_calls",
                        }
                    ]
                }

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
            # print(value)
            yield value

    return generate, generate_stream
