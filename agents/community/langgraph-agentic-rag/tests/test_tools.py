import os
from ibm_watsonx_ai import Credentials, APIClient

from utils import load_config, load_dotenv_with_current_path
from langgraph_agentic_rag import retriever_tool_watsonx

load_dotenv_with_current_path()
config = load_config()

deployment_config = config["deployment"]
parameters = deployment_config["online"]["parameters"]

credentials = Credentials(
    url=deployment_config["watsonx_url"],
    api_key=deployment_config["watsonx_apikey"],
)

api_client = APIClient(credentials, space_id=os.environ["WATSONX_SPACE_ID"])

embedding_model_id = parameters["embedding_model_id"]
vector_store_connection_id = parameters["vector_store_connection_id"]
vector_store_index_name = parameters["vector_store_index_name"]


class TestTools:
    def test_dummy_vector_index_run(self):
        query = "IBM"

        rag_tool = retriever_tool_watsonx(
            api_client,
            embedding_model_id,
            vector_store_connection_id,
            vector_store_index_name,
        )

        result = rag_tool.invoke({"query": query})
        assert isinstance(result, str)
