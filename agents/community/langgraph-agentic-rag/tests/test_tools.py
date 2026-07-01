from ibm_watsonx_ai import Credentials, APIClient

from utils import load_config
from langgraph_agentic_rag import retriever_tool_watsonx

config = load_config()

dep_config = config["deployment"]

api_client = APIClient(
    credentials=Credentials(
        url=dep_config["watsonx_url"], api_key=dep_config["watsonx_apikey"]
    )
)

tool_config = {
    "spaceId": dep_config["online"]["parameters"]["tool_config_spaceId"],
    "vectorIndexId": dep_config["online"]["parameters"]["tool_config_vectorIndexId"],
}


class TestTools:
    def test_dummy_vector_index_run(self):
        query = "IBM"
        rag_tool = retriever_tool_watsonx(api_client, tool_config)
        result = rag_tool.invoke({"query": query})
        assert isinstance(result, str)
