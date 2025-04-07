from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class WebSearchInputSchema(BaseModel):
    """Input schema for WebSearchInputSchema."""

    argument: str = Field(..., description="Description of the argument.")


class WebSearchTool(BaseTool):
    name: str = "DummyWebSearch"
    description: str = (
        "Clear description for what this tool is useful for, you agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = WebSearchInputSchema

    def _run(self, argument: str) -> list[str]:
        # return dummy data
        return ["IBM watsonx.ai"]
