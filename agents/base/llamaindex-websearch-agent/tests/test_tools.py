from llama_index_workflow_agent_base import dummy_web_search


class TestTools:
    def test_dummy_web_search(self):
        query = "IBM"
        result = dummy_web_search(query)
        assert "IBM" in result[0]
