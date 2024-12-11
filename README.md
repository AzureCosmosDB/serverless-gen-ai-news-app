# Project

This is a GenAI news aggregator and summarizer app to answer any queries related to latest news in natural language. This is a serverless GenAI application built using Azure Functions, Azure Cosmos DB and Azure OpenAI.

Prerequisites to run locally:
1. Visual Studio Code
2. Install necessary dependencies to [Run Azure Functions locally in Vscode](https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code?tabs=node-v4%2Cpython-v2%2Cisolated-process%2Cquick-create&pivots=programming-language-python) 
3. Install necessary dependencies to [Run Azure Static web apps locally in Vscode](https://learn.microsoft.com/en-us/azure/static-web-apps/local-development)

This repository has 3 main components:

### 1. Static-web-app

This is the Azure static web app to host the frontend chat interface of the application. This is written in JS & HTML and uses static web app for Azure deployment. 
Steps to run locally:
```bash
cd {workspace-folder}/static-web-app
swa start .
```
The web interface can be accessed using http://localhost:4280.

### 2. Chat-functions-app

This is an HTTP trigger Azure Functions app. Any request made from the static web-app is routed to this functions app, which in turn calls Azure OpenAI's chat completion API to generate natural language response. 

Steps to run locally:
```bash
cd {workspace-folder}/chat-functions-app
func start
```

### 3. Ingestion-functions-app

This is a timer trigger Azure Functions app. This app periodically aggregates data from Google News API and process the RSS feed to filter news article and metadata associated with it to store in Azure Cosmos DB along with its vector embeddings.

Steps to run locally:
```bash
cd {workspace-folder}/ingestion-functions-app
func start
```

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
