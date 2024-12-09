from azure.cosmos import CosmosClient
from azure.cosmos import PartitionKey, exceptions
import yaml
import os

class CosmosDBClient:
    config_file_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_file_path, "r") as file:
        config = yaml.safe_load(file)
        COSMOS_DB_ENDPOINT = config['cosmos_db_endpoint']
        COSMOS_DB_KEY = os.environ['cosmos_db_key']
        DATABASE_NAME = config['database_name']
        CONTAINER_NAME = config['container_name']
        CACHE_CONTAINER_NAME = config['cache_container_name']
        OPEN_AI_EMBEDDING_DIMENSION = config['openai_embeddings_dimensions']

    def __init__(self):
        self.client = CosmosClient(self.COSMOS_DB_ENDPOINT, self.COSMOS_DB_KEY)
        self.db = self.client.create_database_if_not_exists(self.DATABASE_NAME)
        
        # Create the vector embedding policy to specify vector details
        vector_embedding_policy = {
            "vectorEmbeddings": [ 
                { 
                    "path":"/vector",
                    "dataType":"float32",
                    "distanceFunction":"cosine",
                    "dimensions": int(self.OPEN_AI_EMBEDDING_DIMENSION)
                }, 
            ]
        }

        # Create the vector index policy to specify vector details
        indexing_policy = {
            "includedPaths": [ 
            { 
                "path": "/*" 
            } 
            ], 
            "excludedPaths": [ 
            { 
                "path": "/\"_etag\"/?",
                "path": "/vector/*",
            } 
            ], 
            "vectorIndexes": [ 
                {
                    "path": "/vector", 
                    "type": "quantizedFlat" 
                }
            ]
        } 

        # Create the data collection with vector index (note: this creates a container with 10000 RUs to allow fast data load)
        try:
            self.container = self.db.create_container_if_not_exists(id=self.CONTAINER_NAME, 
                                                        partition_key=PartitionKey(path='/category'), 
                                                        indexing_policy=indexing_policy,
                                                        vector_embedding_policy=vector_embedding_policy) 
            print('Container with id \'{0}\' created'.format(self.container.id)) 

        except exceptions.CosmosHttpResponseError: 
            raise 

        # Create the cache collection with vector index
        try:
            self.cache_container = self.db.create_container_if_not_exists(id=self.CACHE_CONTAINER_NAME, 
                                                        partition_key=PartitionKey(path='/id'), 
                                                        indexing_policy=indexing_policy,
                                                        vector_embedding_policy=vector_embedding_policy) 
            print('Container with id \'{0}\' created'.format(self.cache_container.id)) 

        except exceptions.CosmosHttpResponseError: 
            raise

    def write_articles(self, articles):
        for article in articles:
            print(f"Writing article: {article}")
            self.container.upsert_item(article)

    # Perform a vector search on the Cosmos DB container
    def vector_search(self, container, vectors, similarity_score=0.1, num_results=3):
        # Execute the query
        results = container.query_items(
            query= '''
            SELECT TOP @num_results  c.content, VectorDistance(c.vector, @embedding) as SimilarityScore 
            FROM c
            WHERE VectorDistance(c.vector,@embedding) > @similarity_score
            ORDER BY VectorDistance(c.vector,@embedding)
            ''',
            parameters=[
                {"name": "@embedding", "value": vectors},
                {"name": "@num_results", "value": num_results},
                {"name": "@similarity_score", "value": similarity_score}
            ],
            enable_cross_partition_query=True, populate_query_metrics=True)
        results = list(results)
        print(f"Found {len(results)} similar articles")
        # Extract the necessary information from the results
        formatted_results = []
        for result in results:
            score = result.pop('SimilarityScore')
            formatted_result = {
                'SimilarityScore': score,
                'document': result
            }
            formatted_results.append(formatted_result)

        # #print(formatted_results)
        metrics_header = dict(container.client_connection.last_response_headers)
        #print(json.dumps(metrics_header,indent=4))
        return formatted_results