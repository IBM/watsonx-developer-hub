import urllib
from langgraph.checkpoint.postgres import PostgresSaver
from utils import load_config, generate_database_URI
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.deployments import RuntimeContext

thread_id = "PLACEHOLDER FOR YOUR THREAD ID"

config = load_config()
dep_config = config["deployment"]
online_parameters = dep_config["online"]["parameters"]


hostname = urllib.parse.urlparse(dep_config["watsonx_url"]).hostname or ""
is_cloud_url = hostname.lower().endswith("cloud.ibm.com")
instance_id = None if is_cloud_url else "openshift"

url = dep_config["watsonx_url"]
api_key = dep_config["watsonx_apikey"]
space_id = dep_config["space_id"]
db_connection_id = dep_config["online"]["parameters"]["postgres_db_conenction_id"]

client = APIClient(
    credentials=Credentials(url=url, api_key=api_key, instance_id=instance_id),
    space_id=space_id,
)

DB_URI = generate_database_URI(client, db_connection_id)

with PostgresSaver.from_conn_string(DB_URI) as saver:
    saver.delete_thread(thread_id)

print(f"Successfully deleted conversation with id: {thread_id}")