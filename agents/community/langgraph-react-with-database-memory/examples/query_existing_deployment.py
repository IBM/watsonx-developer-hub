import ibm_watsonx_ai

from utils import load_config
from examples._interactive_chat import InteractiveChat
import uuid

deployment_id = "PLACEHOLDER FOR YOUR DEPLOYMENT ID"
thread_id = "PLACEHOLDER FOR YOUR THREAD ID"
stream = True
config = load_config("deployment")

client = ibm_watsonx_ai.APIClient(
    credentials=ibm_watsonx_ai.Credentials(
        url=config["watsonx_url"], api_key=config["watsonx_apikey"]
    ),
    space_id=config["space_id"],
)

if thread_id == "PLACEHOLDER FOR YOUR THREAD ID":
    thread_id = str(uuid.uuid4())

header = f" thread_id: {thread_id} "
print()
print("\u2554" + len(header) * "\u2550" + "\u2557")
print("\u2551" + header + "\u2551")
print("\u255a" + len(header) * "\u2550" + "\u255d")
print()


# Executing deployed AI service with provided scoring data
if stream:
    ai_service_invoke = lambda payload: client.deployments.run_ai_service_stream(
        deployment_id, {**payload, "thread_id": thread_id}
    )
else:
    ai_service_invoke = lambda payload: client.deployments.run_ai_service(
        deployment_id, {**payload, "thread_id": thread_id}
    )

chat = InteractiveChat(ai_service_invoke, stream=stream)
chat.run()
