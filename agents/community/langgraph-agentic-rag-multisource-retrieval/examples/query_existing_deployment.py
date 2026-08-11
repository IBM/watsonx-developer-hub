import ibm_watsonx_ai

from utils import load_config
from examples._interactive_chat import InteractiveChat

deployment_id = "8af73a87-a451-4d64-8dd7-f5fea7abd8c0"
stream = True
config = load_config("deployment")

client = ibm_watsonx_ai.APIClient(
    credentials=ibm_watsonx_ai.Credentials(
        url=config["watsonx_url"], api_key=config["watsonx_apikey"]
    ),
    space_id=config["space_id"],
)

# Executing deployed AI service with provided scoring data
# if stream:
#     ai_service_invoke = lambda payload: client.deployments.run_ai_service_stream(
#         deployment_id, payload
#     )
# else:
#     ai_service_invoke = lambda payload: client.deployments.run_ai_service(
#         deployment_id, payload
#     )

# chat = InteractiveChat(ai_service_invoke, stream=stream)
# chat.run()

payload = {
    "messages": [
        {
        "role": "user",
        "content": "what's ibm's carbon emission"
        }
    ]
    }

for chunk in client.deployments.run_ai_service_stream(deployment_id, payload):
    print(chunk)

