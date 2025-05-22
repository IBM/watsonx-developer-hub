from langgraph_react_with_database_memory import (
    dummy_web_search
)


class TestTools:
    def test_dummy_web_search(self):
        query = "IBM"
        result = dummy_web_search.invoke(query)
        assert "IBM" in result[0]  # Check if the result contains 'IBM'
