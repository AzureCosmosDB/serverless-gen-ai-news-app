import azure.functions as func
import datetime
import logging
import news_processing
import requests
from openai_client import OpenAIClient
import hashlib
import os

app = func.FunctionApp()

@app.function_name(name="news-ingestion-app")
@app.timer_trigger(schedule="0 */15 * * * *",
                   arg_name="mytimer",
                   run_on_startup=False)
@app.cosmos_db_output(arg_name="documents",
                     database_name="News",
                     container_name="NewsArticles",
                     create_if_not_exists=False,
                     connection="cosmoddbconnection")
async def main(mytimer: func.TimerRequest, documents: func.Out[func.Document]):
    utc_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if mytimer.past_due:
        logging.info("The timer is past due!")
    logging.info("Python timer trigger function ran at %s", utc_timestamp)

    try:
        articles = await fetch_news_articles()
        documents.set([func.Document.from_dict(article) for article in articles])
        logging.info("Stored articles: %s", len(articles))
    except Exception:
        logging.exception("News ingestion failed")
        raise


openai_client = OpenAIClient()


async def fetch_news_articles():
    response = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params={"country": "in"},
        headers={"X-Api-Key": os.environ["news_api_key"]},
        timeout=30,
    )
    response.raise_for_status()
    articles = response.json().get("articles", [])
    logging.info("Fetched articles: %s", len(articles))
    return await process_news_articles(articles)


async def process_article(raw_article):
    try:
        article, final_url = await news_processing.process_urls(raw_article.get("url"))
        if article is not None:
            category = news_processing.infer_category_with_openai(article.title, article.text)
            combined_text = f"title: {article.title} content: {article.text}"
            vector = openai_client.generate_embeddings(combined_text)
            if vector is None:
                return None
            article_id = hashlib.sha256(article.title.encode()).hexdigest()
            processed_article = {
                "id": article_id,
                "source": {
                    "name": raw_article.get("source", {}).get("name"),
                    "url": raw_article.get("url"),
                },
                "title": article.title,
                "author": raw_article.get("author"),
                "publishedDate": str(raw_article.get("publishedAt")),
                "content": article.text,
                "summary": "",
                "url": final_url,
                "vector": vector,
                "tags": list(article.tags),
                "category": category,
            }
            logging.info("Processed article: %s", processed_article["title"])
            return processed_article
    except Exception:
        logging.exception("Error processing article %s", raw_article.get("url"))
    return None


async def process_news_articles(articles):
    processed_articles = []
    for raw_article in articles:
        processed_article = await process_article(raw_article)
        if processed_article is not None:
            processed_articles.append(processed_article)
    return processed_articles
