from ibm_watsonx_ai import Credentials, APIClient

from utils import load_config
from langgraph_sql_rag.tools import sql_tools_watsonx

config = load_config()

dep_config = config["deployment"]

api_client = APIClient(
    credentials=Credentials(
        url=dep_config["watsonx_url"], api_key=dep_config["watsonx_apikey"]
    )
)

tool_config = {
    "connection_id": dep_config["online"]["tool_config_connection_id"],
    "schema": dep_config["online"]["tool_config_schema"],
    "model_id": dep_config["online"]["tool_config_model_id"],
    "dialect": dep_config["online"]["tool_config_dialect"],
}


class TestTools:
    def test_dummy_sql_tools_run(self):
        rag_tools = sql_tools_watsonx(api_client, tool_config)

        assert len(rag_tools) > 0
