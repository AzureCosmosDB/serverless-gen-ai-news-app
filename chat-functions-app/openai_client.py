from openai import AzureOpenAI
from cosmos_client import CosmosDBClient
import yaml
import os
import uuid
import json
import logging


class OpenAIClient:
    config_file_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_file_path, "r") as file:
        config = yaml.safe_load(file)
        openai_endpoint = config['openai_endpoint']
        openai_key = os.environ['openai_key']
        openai_api_version = config['openai_api_version']
        openai_embeddings_deployment = config['openai_embeddings_deployment']
        openai_embeddings_dimensions = int(config['openai_embeddings_dimensions'])
        openai_completions_deployment = config['openai_completions_deployment']

    def __init__(self):
        self.openai_client = AzureOpenAI(azure_endpoint=self.openai_endpoint, api_key=self.openai_key, api_version=self.openai_api_version)
        self.cosmos_client = CosmosDBClient()
        
    # generate openai embeddings
    def generate_embeddings(self, text):    
        '''
        Generate embeddings from string of text.
        This will be used to vectorize data and user input for interactions with Azure OpenAI.
        '''
        response = self.openai_client.embeddings.create(input=text, 
                                                model=self.openai_embeddings_deployment,
                                                dimensions=self.openai_embeddings_dimensions)
        embeddings =response.model_dump()
        return embeddings['data'][0]['embedding']

    def get_chat_history(self, container, completions=3):
        results = container.query_items(
            query= '''
            SELECT TOP @completions *
            FROM c
            ORDER BY c._ts DESC
            ''',
            parameters=[
                {"name": "@completions", "value": completions},
            ], enable_cross_partition_query=True)
        results = list(results)
        return results

    def generate_completion(self, user_prompt, vector_search_results, chat_history):
        
        system_prompt = """You are an intelligent assistant for the Cosmic News app, designed to provide accurate and helpful answers to user queries about the latest news and historical timelines of news events, using only the provided JSON data.
                Instructions:
                - Only reference news articles or events included in the JSON data.
                - If a particular category of news is asked, provide the latest news in that category only.
                - If the data related to user query is not available, politely inform the user that you cannot answer queries about it.
                - If you are unsure of an answer, respond with "I don't know" or "I'm not sure," and suggest the user perform a search on their own.
                Formatting Instructions:
                - Use <h3> for each news headline.
                - Provide concise summaries underneath each headline in <p> tags.
                - For historical news articles, use <h4> for the date in bold, followed by the event description in <p> tags.
                - Assume the user has no prior knowledge of the topic in question.
            """
        #         Instructions:

        #         - If a news event is not included in the provided context, politely inform the user that you cannot answer queries about it.
        #         - Only reference news articles or events included in the JSON data.
        #         - If you are unsure of an answer, respond with "I don't know" or "I'm not sure," and suggest the user perform a search on their own.
        #         - Decline to answer any questions unrelated to news and politely remind the user that you are a news assistant.
        #         - Ensure your response is clear, complete, and suitable for display on a web page.
        #         
        
        # Create a list of messages as a payload to send to the OpenAI Completions API

        # system prompt
        messages = [{'role': 'system', 'content': system_prompt}]

        #chat history
        for chat in chat_history:
            if chat['prompt'] and chat['completion']:
                messages.append({'role': 'user', 'content': chat['prompt'] + " " + chat['completion']})
        
        #user prompt
        messages.append({'role': 'user', 'content': user_prompt})

        #vector search results
        for result in vector_search_results:
            if result['document']:
                messages.append({'role': 'system', 'content': json.dumps(result['document'])})

        # Create the completion
        response = self.openai_client.chat.completions.create(
            model = self.openai_completions_deployment,
            messages = messages,
            temperature = 0.1
        )    
        return response.model_dump()

    
    def chat_completion(self, cache_container, container, user_input):
        print("starting completion")
        # Generate embeddings from the user input
        user_embeddings = self.generate_embeddings(user_input)
        #perform vector search on the news container
        logging.info("New result\n")
        search_results = self.cosmos_client.vector_search(container, user_embeddings)
        logging.info("Getting Chat History\n")
        #chat history
        chat_history = self.get_chat_history(cache_container, 3)
        #generate the completion
        logging.info("Generating completions \n")
        completions_results = self.generate_completion(user_input, search_results, chat_history)
        
        #cache the response
        if completions_results['choices'][0]['message']['content']: 
            logging.info("Caching response \n")
            self.cache_response(cache_container, user_input, user_embeddings, completions_results)
            return completions_results['choices'][0]['message']['content'], False
        # Return the default completion
        return "I apologize for not answering this question. Please ask another question.", False
    
    def cache_response(self, container, user_prompt, prompt_vectors, response):
        # Create a dictionary representing the chat document
        chat_document = {
            'id':  str(uuid.uuid4()),  
            'prompt': user_prompt,
            'completion': response['choices'][0]['message']['content'],
            'completionTokens': str(response['usage']['completion_tokens']),
            'promptTokens': str(response['usage']['prompt_tokens']),
            'totalTokens': str(response['usage']['total_tokens']),
            'model': response['model'],
            'vector': prompt_vectors
        }
        # Insert the chat document into the Cosmos DB container
        container.create_item(body=chat_document)