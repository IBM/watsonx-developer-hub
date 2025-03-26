def deployable_ai_service(context, **custom):
    from ibm_watsonx_ai import Credentials
    from autogen_agent_base.agent import get_workflow_closure
    from autogen_agentchat.ui import Console

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
        credentials = (
            Credentials(url=custom.get("url"), api_key=custom.get("api_key")),
        )
        agent = get_workflow_closure(credentials, model_id, custom.get("space_id"))

        payload = context.get_json()
        messages = payload.get("messages", [])

        stream = agent.run_stream(task=messages)
        return await Console(stream)
