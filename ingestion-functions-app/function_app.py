import azure.functions as func
import datetime
import logging
import news_processing
import requests
from openai_client import OpenAIClient
import hashlib

app = func.FunctionApp()

@app.function_name(name="news-ingestion-app")
@app.timer_trigger(schedule="0 */15 * * * *", 
              arg_name="mytimer",
              run_on_startup=True) 
@app.cosmos_db_output(arg_name="documents", 
                      database_name="News",
                      container_name="NewsArticles",
                      create_if_not_exists=True,
                      connection="cosmoddbconnection")
async def main(mytimer: func.TimerRequest, documents: func.Out[func.Document]):
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    
    if mytimer.past_due:
        logging.info('The timer is past due!')
    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    try:
        articles = await fetch_news_articles()
        # Convert each article to a Document and append to the output
        docs_to_store = [func.Document.from_dict(article) for article in articles]
        # Store all documents at once
        documents.set(docs_to_store)
        logging.info(f"Stored articles: {len(docs_to_store)}")
    except Exception as e:
        logging.error('Error:')
        logging.error(e)

openai_client = OpenAIClient()
# Init
api_key='fb8fa1da87d1482081783da21aa77cf8'

def fetch_news_articles():
    url = 'https://newsapi.org/v2/top-headlines?country=in&apiKey='+api_key
    articles = []
    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json()
        articles = news_data.get("articles", [])
        print(f"Total articles: {len(articles)}" + "\n")
    else:
        print(f"Error fetching articles: {response.text}" + "\n")
    return process_news_articles(articles)

async def process_article(raw_article):
    try:
        article, final_url = await news_processing.process_urls(raw_article.get("url"))
        if article is not None:
            # Infer the category of the article
            category = news_processing.infer_category_with_openai(article.title, article.text)
            logging.info(f"Category: {category}")
            combined_text = f"title: {article.title} content: {article.text}"
            vector = openai_client.generate_embeddings(combined_text)
            if vector is None:
                return None
            hash_object = hashlib.sha256(article.title.encode())
            id = hash_object.hexdigest()
            processed_article = {
                "id": id,
                "source": {
                    "name": raw_article.get("source", {}).get("name"),
                    "url": raw_article.get("url")
                },
                "title": article.title,
                "author": raw_article.get("author"),
                "publishedDate": str(raw_article.get("publishedAt")),
                "content": article.text,
                "summary": "",  # Summarization to be handled separately
                "url": final_url,
                "vector": vector,  
                "tags": list(article.tags) ,  
                "category": category 
            }
            logging.info(f"Processed article: {processed_article['title']}")
            return processed_article
    except Exception as e:
        print(f"Error processing article {raw_article.get('url')}: {e}")
    return None

async def process_news_articles(articles):
    processed_articles = []
    for raw_article in articles:
        processed_article = await process_article(raw_article)
        if processed_article is not None:
            processed_articles.append(processed_article)
    # # Close the browser and return the processed articles
    return processed_articles

