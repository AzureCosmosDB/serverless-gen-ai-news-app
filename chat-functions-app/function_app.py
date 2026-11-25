import json
import azure.functions as func
import logging
import time 
from openai_client import OpenAIClient
from cosmos_client import CosmosDBClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

cosmos_client = CosmosDBClient()
openai_client = OpenAIClient(cosmos_client)
news_container = cosmos_client.container
cache_container = cosmos_client.cache_container

@app.function_name(name="news-app")
@app.route(route="query", methods=["POST"])
def chat_query(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "request body must be valid JSON"}),
            status_code=400, mimetype="application/json")

    if not isinstance(body, dict):
        return func.HttpResponse(
            json.dumps({"error": "request body must be a JSON object"}),
            status_code=400, mimetype="application/json")

    message = body.get("message")
    chat_history = body.get("chatHistory", [])
    if not isinstance(message, str) or not message.strip() or not isinstance(chat_history, list):
        return func.HttpResponse(
            json.dumps({"error": "message must be nonempty text and chatHistory must be a list"}),
            status_code=400, mimetype="application/json")

    try:
        response, cached = user(message, chat_history)
        json_response = json.dumps({"response": response, "cached": cached})
        return func.HttpResponse(json_response, status_code=200, mimetype="application/json")
    except Exception:
        logging.exception("Error while executing chat request")
        return func.HttpResponse(
            json.dumps({"error": "Unable to process the news query. Please try again."}),
            status_code=500, mimetype="application/json")
    
    
def user(user_message, chat_history):
        # Get LLM completion
        response_payload, cached = openai_client.chat_completion(cache_container, news_container, user_message)
        chat_history.append([user_message, response_payload])
        return response_payload, cached