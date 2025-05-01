def deployable_ai_service(context, url = None, project_id = None, model_id = None):
    import asyncio
    import nest_asyncio
    import threading
    from datetime import date
    from beeai_framework_workflow_base.workflow import get_beeai_framework_workflow
    from beeai_framework.backend.message import (
        Message,
    )
    from beeai_framework.workflows.agent import AgentWorkflowInput


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

    def get_formatted_message(final_answer: str) -> dict | None:
        return {"role": "assistant", "content": final_answer}

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
        workflow = get_beeai_framework_workflow(token, url, model_id, project_id)

        payload = context.get_json()
        messages = payload.get("messages", [])
        input_prompt = ''.join(message["content"] for message in messages)
        today = date.today().strftime("%B %d, %Y")
        
        response = await (
            workflow.run(
                inputs=[
                    AgentWorkflowInput(
                        prompt=f"Provide a comprehensive weather summary for {input_prompt} from {today}.",
                        expected_output="Essential weather details such as chance of rain, temperature and wind. Only report information that is available.",
                    ),
                    AgentWorkflowInput(
                        prompt=f"Search for a set of activities close to {input_prompt} from {today} that are appropriate in light of the weather conditions.",
                        expected_output="A list of activities including location and description that are weather appropriate.",
                    ),
                    AgentWorkflowInput(
                        prompt=f"Consider the weather report and recommended activities for the trip to {input_prompt} from {today} and provide a coherent summary.",
                        expected_output="A summary of the trip that the traveler could take with them. Break it down by day including weather, location and helpful tips.",
                    ),
                ]
            )
            .on(
                "success",
                lambda data, event: print(
                    f"-> Step '{data.step}' has been completed with the following outcome.\n\n{data.state.final_answer}"
                ),
            )
        )

        return response.state.final_answer

    def generate(context) -> dict:
        """
        A synchronous wrapper for the asynchronous `generate_async` method.
        """

        future = asyncio.run_coroutine_threadsafe(
            generate_async(context), persistent_loop
        )
        choices = []

        output = get_formatted_message(future.result())

        if output:
            choices.append({"index": 0, "message": output})
        
        return {
            "headers": {"Content-Type": "application/json"},
            "body": {"choices": choices},
        }

    return (generate,)
