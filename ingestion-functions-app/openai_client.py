from openai import AzureOpenAI
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
        openai_key = config['openai_key']
        openai_api_version = config['openai_api_version']
        openai_embeddings_deployment = config['openai_embeddings_deployment']
        openai_embeddings_dimensions = int(config['openai_embeddings_dimensions'])
        openai_completions_deployment = config['openai_completions_deployment']

    def __init__(self):
        self.openai_client = AzureOpenAI(azure_endpoint=self.openai_endpoint, api_key=self.openai_key, api_version=self.openai_api_version)
        #self.cosmos_client = CosmosDBClient()
        
    # generate openai embeddings
    def generate_embeddings(self, text):    
        '''
        Generate embeddings from string of text.
        This will be used to vectorize data and user input for interactions with Azure OpenAI.
        '''
        try:
            response = self.openai_client.embeddings.create(input=text, 
                                                    model=self.openai_embeddings_deployment,
                                                    dimensions=self.openai_embeddings_dimensions)
            embeddings =response.model_dump()
            return embeddings['data'][0]['embedding']
        except Exception as e:
            logging.error(f"Error generating embeddings: {e}")
            return None
        
    def categorize_article(self, title, content):
        prompt = ("Given the title and content of the news article, identify the most relevant category among the following: \n"
                 "World, Technology, Health, Entertainment, Sports, Business, Politics, Science, Economy, Opinion, Crime, Education, Environment, Lifestyle, Culture, Travel, or Other. \n"
                "Give only one word category as the answer."
                "Don't provide full sentences or explanations, just the category.")

        # system prompt
        messages = [{'role': 'system', 'content': prompt}]

        # user prompt
        messages.append({'role': 'user', 'content': f"Title: {title}\n\nContent: {content}"})

        # Make the API call to OpenAI
        response = self.openai_client.chat.completions.create(
            model= self.openai_completions_deployment, 
            messages=messages,
            max_tokens=100,  # Limit the response length
            temperature=0.0,  # Lower temperature for deterministic results
            n=1,  # Number of completions to generate
            stop=None  # End the output when OpenAI detects the end of the prompt
        )

        # Extract the category from the response
        category = response.model_dump()['choices'][0]['message']['content']
        return category

    # def get_chat_history(self, container, completions=3):
    #     results = container.query_items(
    #         query= '''
    #         SELECT TOP @completions *
    #         FROM c
    #         ORDER BY c._ts DESC
    #         ''',
    #         parameters=[
    #             {"name": "@completions", "value": completions},
    #         ], enable_cross_partition_query=True)
    #     results = list(results)
    #     return results

    # def generate_completion(self, user_prompt, vector_search_results, chat_history):
        
    #     system_prompt = '''
    #     You are an intelligent assistant for news aggregation. You are designed to provide concise, relevant, and factual summaries in response to user queries about news in your database.
    #         - Summarize only the information directly related to the user’s query.
    #         - Ignore any information that is not relevant to the user’s query or the provided articles.
    #         - Do not include unrelated details or speculate beyond the provided information.
    #         - Respond only to questions directly connected to the summarized content.
    #         - Avoid providing answers or details on topics not covered in the provided information.
    #     '''

    #     # Create a list of messages as a payload to send to the OpenAI Completions API

    #     # system prompt
    #     messages = [{'role': 'system', 'content': system_prompt}]

    #     #chat history
    #     for chat in chat_history:
    #         messages.append({'role': 'user', 'content': chat['prompt'] + " " + chat['completion']})
        
    #     #user prompt
    #     messages.append({'role': 'user', 'content': user_prompt})

    #     #vector search results
    #     for result in vector_search_results:
    #         messages.append({'role': 'system', 'content': json.dumps(result['document'])})

    #     print("Messages going to openai", messages)
    #     # Create the completion
    #     response = self.openai_client.chat.completions.create(
    #         model = self.openai_completions_deployment,
    #         messages = messages,
    #         temperature = 0.1
    #     )    
    #     return response.model_dump()

    
    # def chat_completion(self, cache_container, container, user_input):
    #     print("starting completion")
    #     # Generate embeddings from the user input
    #     user_embeddings = self.generate_embeddings(user_input)

    #     #perform vector search on the news container
    #     print("New result\n")
    #     search_results = self.cosmos_client.vector_search(container, user_embeddings)
    #     print("Getting Chat History\n")
    #     #chat history
    #     chat_history = self.get_chat_history(cache_container, 3)
    #     #generate the completion
    #     print("Generating completions \n")
    #     completions_results = self.generate_completion(user_input, search_results, chat_history)
    #     print("Caching response \n")
    #     #cache the response
    #     self.cache_response(cache_container, user_input, user_embeddings, completions_results)
    #     print("\n")
    #     # Return the generated LLM completion
    #     return completions_results['choices'][0]['message']['content'], False
    
    # def cache_response(self, container, user_prompt, prompt_vectors, response):
    #     # Create a dictionary representing the chat document
    #     chat_document = {
    #         'id':  str(uuid.uuid4()),  
    #         'prompt': user_prompt,
    #         'completion': response['choices'][0]['message']['content'],
    #         'completionTokens': str(response['usage']['completion_tokens']),
    #         'promptTokens': str(response['usage']['prompt_tokens']),
    #         'totalTokens': str(response['usage']['total_tokens']),
    #         'model': response['model'],
    #         'vector': prompt_vectors
    #     }
    #     # Insert the chat document into the Cosmos DB container
    #     container.create_item(body=chat_document)