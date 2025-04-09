def deployable_ai_service(context, url = None, project_id = None, model_id = None):
    import asyncio
    import nest_asyncio
    import threading
    from beeai_framework_react_agent_base.agent import get_beeai_framework_agent
    from beeai_framework.agents.types import AgentExecutionConfig
    from beeai_framework.backend.message import (
        Message,
        SystemMessage,
    )


    nest_asyncio.apply() # Inject support for nested event loops

    persistent_loop = (
        asyncio.new_event_loop()
    ) # Create a persistent event loop that will be used by generate and generate_stream

    def start_loop(loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    threading.Thread(
        target=start_loop, args=(persistent_loop,), daemon=True
    ).start() # Run a persistent loop in a separate daemon thread

    def get_formatted_message(resp: Message) -> dict | None:
        role = resp.role
        if resp.content:
            if role == "assistant":
                return {"role": role, "content": ''.join(message.text for message in resp.content)}
            elif role == "tool":
                return {
                    "role": role,
                    "tool_call_id": resp.tool.call_id,
                    "name": resp.tool_name,
                    "content": resp.content,
                }


    async def generate_async(context) -> dict:
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

        token=context.get_token()

        agent = get_beeai_framework_agent(token, url, model_id, project_id)
        system_message = SystemMessage(content="You are a helpful AI assistant, please respond to the user's query to the best of your ability!")
        await agent.memory.add(system_message)

        payload = context.get_json()

        prompt = ""
        for message in payload.get("messages", []):
            prompt += "{}:\n{}\n\n".format(message["role"].upper(), message["content"])
    
        response = await agent.run(
             prompt,
             execution=AgentExecutionConfig(max_retries_per_step=3, total_max_retries=10, max_iterations=20),
        )

        return response

    def generate(context) -> dict:
        """
        A synchronous wrapper for the asynchronous `generate_async` method.
        """

        future = asyncio.run_coroutine_threadsafe(
            generate_async(context), persistent_loop
        )
        choices = []
        generated_response = future.result()

        output = get_formatted_message(generated_response.result)
        if output is not None:
            choices.append({"index": 0, "message": output})
        
        return {
            "headers": {"Content-Type": "application/json"},
            "body": {"choices": choices},
        }

    return (generate,)
