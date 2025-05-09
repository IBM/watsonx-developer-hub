# Apps

A catalog of apps that are designed to help users infer with deployed agents.

## Key features

- 🌐 **Framework agnostic**: Build apps with any framework.
- ☁️ **Deployment**: Deploy apps with one command.

## Get started

1. **Install** the CLI 

```bash
pip install ibm-watsonx-ai-cli
```

2. **Download** the app
```bash
watsonx-ai app new
```

3. **Configure** the app

Go to the [Developer Access](https://dataplatform.cloud.ibm.com/developer-access) to find your environment variables also retrieve deployment url/deployment_id for deployed template from the link provided afer deployment.
Note that the value of the **WATSONX_BASE_DEPLOYMENT_URL** needs to end with the deployment guid as we will be
crafting multiple URLs based on that base. Example of **WATSONX_BASE_DEPLOYMENT_URL**:
`https://us-south.ml.cloud.ibm.com/ml/v4/deployments/{deployment_id}`

```bash
cd <app_name>
cp template.env .env
```

4. **Start** the app

```bash
watsonx-ai app run
```

4. **Start** the app in development mode

```bash
watsonx-ai app run --dev
```
This soultion allows user to make changes to the source code while the app is running. Each time changes are saved the app reloads and is working with provided changes.


## Official Apps

| Template                              | Framework | Description                                                  |
| ------------------------------------- | --------- | ------------------------------------------------------------ |
| [React UI](./base/nextjs-chat-with-ai-service/) | Next.js   | App to infer with deployed agents providing a chat interface |
