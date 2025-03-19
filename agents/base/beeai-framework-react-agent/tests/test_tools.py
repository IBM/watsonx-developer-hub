import pytest

from beeai_framework.tools import StringToolOutput
from beeai_framework_react_agent_base import (
    dummy_web_search
)


class TestTools:
    @pytest.mark.asyncio
    async def test_tool_web_search(self):
        query = "IBM"
        result: StringToolOutput = await dummy_web_search.run({"query": query})
        assert "IBM" in result.get_text_content()  # Check if the result contains 'IBM'
