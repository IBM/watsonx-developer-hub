from ibm_watsonx_ai import Credentials, APIClient

from utils import load_config
from langgraph_tavily_tool import tavily_search_watsonx

config = load_config()

dep_config = config["deployment"]
service_manager_service_url = dep_config["online"]["parameters"][
    "service_manager_service_url"
]
secret_id = dep_config["online"]["parameters"]["secret_id"]

api_client = APIClient(
    credentials=Credentials(
        url=dep_config["watsonx_url"], api_key=dep_config["watsonx_apikey"]
    )
)


class TestTools:
    def test_tavily_search_watsonx_run(self):
        query = "IBM"
        rag_tool = tavily_search_watsonx(
            api_client, service_manager_service_url, secret_id
        )
        result = rag_tool.invoke({"query": query})
        assert "IBM" in result
