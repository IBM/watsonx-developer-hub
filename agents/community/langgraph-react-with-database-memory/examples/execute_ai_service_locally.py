from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.deployments import RuntimeContext

from ai_service import deployable_ai_service
from utils import load_config
from examples._interactive_chat import InteractiveChat
import uuid

thread_id = "PLACEHOLDER FOR YOUR THREAD ID"

stream = True
config = load_config()
dep_config = config["deployment"]
online_parameters = dep_config["online"]["parameters"]

client = APIClient(
    credentials=Credentials(
        url=dep_config["watsonx_url"], api_key=dep_config["watsonx_apikey"]
    ),
    space_id=dep_config["space_id"],
)

context = RuntimeContext(api_client=client)
ai_service_resp_func = deployable_ai_service(context=context, **online_parameters)[
    stream
]

if thread_id == "PLACEHOLDER FOR YOUR THREAD ID":
    thread_id = str(uuid.uuid4())

header = f" thread_id: {thread_id} "
print()
print("\u2554" + len(header) * "\u2550" + "\u2557")
print("\u2551" + header + "\u2551")
print("\u255a" + len(header) * "\u2550" + "\u255d")
print()


def ai_service_invoke(payload):
    payload["thread_id"] = thread_id
    context.request_payload_json = payload
    return ai_service_resp_func(context)


chat = InteractiveChat(ai_service_invoke, stream=stream)
chat.run()
