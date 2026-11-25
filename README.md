# Project

This is a GenAI news aggregator and summarizer app to answer any queries related to latest news in natural language. This is a serverless GenAI application built using Azure Functions, Azure Cosmos DB and Azure OpenAI.

Prerequisites to run locally:
1. Visual Studio Code
2. Install necessary dependencies to [Run Azure Functions locally in Vscode](https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code?tabs=node-v4%2Cpython-v2%2Cisolated-process%2Cquick-create&pivots=programming-language-python) 
3. Install necessary dependencies to [Run Azure Static web apps locally in Vscode](https://learn.microsoft.com/en-us/azure/static-web-apps/local-development)
4. Python supported by your Azure Functions runtime, Azure Functions Core Tools v4, and Node.js for the frontend tests.

Before starting the Functions apps, create a virtual environment in each app directory,
activate it, and run `python -m pip install -r requirements.txt`. Copy each
`local.settings.json.sample` to `local.settings.json` and populate its empty settings
using your own credentials. Never commit the populated files.

The chat app requires `cosmos_db_key` and `openai_key`. Ingestion requires
`openai_key`, `news_api_key`, and `cosmoddbconnection` (the Cosmos DB connection
string; the spelling must match the output binding). Start Azurite when using
`UseDevelopmentStorage=true`. In Azure, configure these values in each Function
App's application settings, not in the checked-in YAML.

Update both `config.yaml` files for your account, Azure OpenAI deployments, and
supported API version. Both apps must use the same news database, container,
and embedding dimensions. The ingestion output binding currently names `News`
and `NewsArticles`; update it too if you choose different names.

The apps use existing Cosmos containers by default. Provision and verify the
vector capability, embedding policy, and index before ingestion. For an explicitly
approved initial setup, the chat directory's `CosmosDBClient(create_resources=True)`
can create missing containers using the configured policies. Normal app startup
does not create containers or update existing policies.

Any credential previously committed to source must be revoked and replaced.
Removing it from the current files does not remove it from Git history.

This repository has 3 main components:

### 1. Static-web-app

This is the Azure static web app to host the frontend chat interface of the application. This is written in JS & HTML and uses static web app for Azure deployment. 
Steps to run locally:
```bash
cd {workspace-folder}/static-web-app
npm start
```
The web interface can be accessed using http://localhost:8000. No npm dependency
installation is needed for this plain static frontend. Local requests go to
`http://localhost:7071/api/query` (or the corresponding `127.0.0.1` address).
For another API endpoint, define `window.NEWS_API_ENDPOINT` in a script before
`app.js`. The deployed frontend retains the existing Azure Functions endpoint
unless overridden. Ensure that the API permits the frontend origin in CORS.

### 2. Chat-functions-app

This is an HTTP trigger Azure Functions app. Any request made from the static web-app is routed to this functions app, which in turn calls Azure OpenAI's chat completion API to generate natural language response. 

Steps to run locally:
```bash
cd {workspace-folder}/chat-functions-app
func start --port 7071
```

### 3. Ingestion-functions-app

This is a timer-triggered Azure Functions app. Its current entry point retrieves
NewsAPI top headlines, parses article URLs, and stores article metadata and
vector embeddings in Azure Cosmos DB. Google News URL decoding is a helper,
not the current feed source.

Steps to run locally:
```bash
cd {workspace-folder}/ingestion-functions-app
func start --port 7072
```

The timer is not invoked on startup, but it runs on its configured schedule and
writes to Cosmos DB and calls Azure OpenAI. Do not start it against a production
account merely to test local setup. Set
`AzureWebJobs.news-ingestion-app.Disabled` to `true` in local settings if you need
to inspect the host without ingestion.

## Verification and deployment

Offline regression checks, from the repository root with Python dependencies installed:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m pip check
node --test tests/frontend.test.cjs
```

These tests use mocked external services. They do not establish live Azure OpenAI
access, successful Cosmos queries, or ingestion of real news.

The GitHub workflow runs these checks before deploying only `static-web-app`.
Draft pull requests run checks without deploying previews. Marking a PR ready
for review enables the preview deployment.
The two Azure Functions apps require separate deployment and application settings.
An existing Cosmos DB account alone does not establish that the website, API, and
ingestion apps are deployed or healthy.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
