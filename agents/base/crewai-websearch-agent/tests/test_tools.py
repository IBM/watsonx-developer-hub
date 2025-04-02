from crewai_web_search.tools import WebSearchTool


class TestTools:
    def test_dummy_web_search(self):
        query = "IBM"
        result = WebSearchTool().run(query)
        assert "IBM" in result[0]  # Check if the result contains 'IBM'
