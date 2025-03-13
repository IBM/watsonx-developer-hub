from beeai_framework_react_agent_base import (
    dummy_web_search
)


class TestTools:
    def test_dummy_web_search(self):
        query = "IBM"
        result = dummy_web_search.run(query)
        assert "IBM" in result[0]  # Check if the result contains 'IBM'
