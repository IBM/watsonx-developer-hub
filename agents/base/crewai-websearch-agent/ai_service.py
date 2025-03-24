def deployable_ai_service(context, url = None, project_id = None, model_id = None):
    """AI service with AI Assistance Crew that can be deployed to a server."""
    from crewai import LLM
    from crewai.agents.parser import AgentAction, AgentFinish
    from crewai.agents.crew_agent_executor import ToolResult

    from assistance_crew.crew import AssistanceAgents

    def convert_step_to_dict(
        crewai_step: AgentAction | AgentFinish | ToolResult,
    ) -> dict | None:
        """Convert CrewAI step objects to chat message dict.

        :param crewai_step: CrewAI step object
        :type crewai_step: AgentAction | AgentFinish | ToolResult
        :return: Chat message dict
        :rtype: dict | None
        """
        if isinstance(crewai_step, AgentAction):
            return {"role": "assistant", "content": crewai_step.result}
        elif isinstance(crewai_step, AgentFinish):
            return {"role": "assistant", "content": crewai_step.output}
        elif isinstance(crewai_step, ToolResult):
            return {"role": "tool", "content": crewai_step.result}

        return None

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
        Also, only last user message will be passed to the model.
        """

        messages = context.get_json()["messages"]

        # Do not include history
        user_question = messages[-1]["content"]
        custom_instruction = ""
        if (message := messages[0])["role"] == "system":
            custom_instruction = message["content"]
        inputs = {
            "user_prompt": user_question,
            "custom_instruction": custom_instruction,
        }
        llm = LLM(
            model=f"watsonx/{model_id}",
            ## watsonx credentials
            token=context.get_token(),
            api_base=url,
            project_id=project_id,
            ## model params
            temperature=0.7,
        )

        intermediate_steps: list = []
        _ = (
            AssistanceAgents(llm=llm, intermediate_steps=intermediate_steps)
            .crew()
            .kickoff(inputs=inputs)
        )

        choices = [
            {"index": 0, "message": convert_step_to_dict(intermediate_steps[-1])}
        ]
        execute_response = {
            "headers": {"Content-Type": "application/json"},
            "body": {"choices": choices},
        }

        return execute_response

    return (generate,)
