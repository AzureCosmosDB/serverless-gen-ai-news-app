import json
import azure.functions as func
import logging
import time 
from openai_client import OpenAIClient
from cosmos_client import CosmosDBClient
from quart import jsonify

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

openai_client = OpenAIClient()
cosmos_client = CosmosDBClient()
news_container = cosmos_client.container
cache_container = cosmos_client.cache_container

@app.function_name(name="news-app")
@app.route(route="query")
def chat_query(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        body =  req.get_json()
        if not body:
            return jsonify({"error": "request body is empty"}), 400

        # Get the request message
        message = body.get("message")
        chat_history = body.get("chatHistory")
        response, cached = user(message, chat_history)
        json_response = json.dumps({"response": response, "cached": cached})
        return func.HttpResponse(json_response,status_code=200)
    except Exception as e:
        logging.error(f"Error while executing request: {e}")
        return func.HttpResponse(json.dumps(f"Error: {e}"), status_code=500)
    
    
def user(user_message, chat_history):
        # Get LLM completion
        response_payload, cached = openai_client.chat_completion(cache_container, news_container, user_message)
        chat_history.append([user_message, response_payload])
        return response_payload, cached