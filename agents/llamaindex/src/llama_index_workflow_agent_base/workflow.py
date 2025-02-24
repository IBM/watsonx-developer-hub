from typing import Any, List

from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import ToolSelection, ToolOutput
from llama_index.core.tools.types import BaseTool
from llama_index.core.llms import ChatMessage
from llama_index.core.workflow import (
    Workflow,
    StartEvent,
    StopEvent,
    Context,
    Event,
    step,
)


class InputEvent(Event):
    input: list[ChatMessage]


class ToolCallEvent(Event):
    tool_calls: list[ToolSelection]


class FunctionCallingAgent(Workflow):
    def __init__(
        self,
        *args: Any,
        llm: FunctionCallingLLM | None = None,
        tools: List[BaseTool] | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.tools = tools or []

        self.llm = llm
        self.memory = ChatMemoryBuffer.from_defaults(llm=self.llm)

        if system_prompt:
            system_msg = ChatMessage(role="system", content=system_prompt)
            self.memory.put(system_msg)

        self.sources = []

    @step
    async def prepare_chat_history(self, ctx: Context, ev: StartEvent) -> InputEvent:

        ctx.write_event_to_stream(ev)

        self.sources = []

        user_input_messages = ev.input

        for user_input in user_input_messages:
            content = (
                user_input["content"][0]["text"]
                if isinstance(user_input["content"], list)
                else user_input["content"]
            )  # Ensures compatibility with UI payloads, which may send content as a list of dictionaries containing 'type' and 'text' keys.
            self.memory.put(ChatMessage(role=user_input["role"], content=content))

        chat_history = self.memory.get()
        return InputEvent(input=chat_history)

    @step
    async def handle_llm_input(
        self, ctx: Context, ev: InputEvent
    ) -> ToolCallEvent | StopEvent:

        ctx.write_event_to_stream(ev)

        chat_history = ev.input
        response = await self.llm.achat_with_tools(
            self.tools, chat_history=chat_history
        )
        self.memory.put(response.message)

        tool_calls = self.llm.get_tool_calls_from_response(
            response, error_on_no_tool_call=False
        )

        chat_history.append(response.message)

        if not tool_calls:
            return StopEvent(result={"response": response, "messages": chat_history})
        else:
            return ToolCallEvent(tool_calls=tool_calls)

    @step
    async def handle_tool_calls(self, ctx: Context, ev: ToolCallEvent) -> InputEvent:

        ctx.write_event_to_stream(ev)

        tool_calls = ev.tool_calls
        tools_by_name = {tool.metadata.get_name(): tool for tool in self.tools}

        tool_msgs = []

        for tool_call in tool_calls:
            tool = tools_by_name.get(tool_call.tool_name)
            additional_kwargs = {
                "tool_call_id": tool_call.tool_id,
                "name": tool.metadata.get_name(),
            }
            if not tool:
                tool_msgs.append(
                    ChatMessage(
                        role="tool",
                        content=f"Tool {tool_call.tool_name} does not exist",
                        additional_kwargs=additional_kwargs,
                    )
                )
                continue

            try:
                tool_output = tool(**tool_call.tool_kwargs)
                self.sources.append(tool_output)
                tool_msgs.append(
                    ChatMessage(
                        role="tool",
                        content=tool_output.content,
                        additional_kwargs=additional_kwargs,
                    )
                )
            except Exception as e:
                tool_msgs.append(
                    ChatMessage(
                        role="tool",
                        content=f"Encountered error in tool call: {e}",
                        additional_kwargs=additional_kwargs,
                    )
                )

        for msg in tool_msgs:
            self.memory.put(msg)

        chat_history = self.memory.get()
        return InputEvent(input=chat_history)
