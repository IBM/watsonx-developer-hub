def deployable_ai_service(context, **custom):
    from ibm_watsonx_ai import APIClient, Credentials
    from beeai_framework_react_agent_base.agent import get_beeai_framework_agent
    from beeai_framework.messages import (
        AssistantMessage,
        CustomMessage,
        SystemMessage,
        UserMessage,
    )

    model_id = custom.get("model_id")
    client = APIClient(
        credentials=Credentials(url=custom.get("url"), token=context.generate_token()),
        space_id=custom.get("space_id"),
    )

    agent = get_beeai_framework_agent(client, custom.get("project_id"), model_id)


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

        # TODO

    def generate_stream(context) -> dict:
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
        # TODO

    return generate, generate_stream
