from urllib.parse import quote
import requests
import json
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from ..crawler.crawler_base import NewsWithSummary
from ..models import user_news_association_table, NewsArticle
from ..utils import llm_generate
from ..crawler.udn_crawler import UDNCrawler

udn_crawler = UDNCrawler()

def import_news(news_data: NewsWithSummary):
    """
    add new to db
    :param news_data: news info
    :return:
    """
    session = Session()
    udn_crawler.save(news_data, session)

def fetch_latest_news_info(search_term: str, is_initial=False):
    """
    get new

    :param search_term:
    :param is_initial:
    :return:
    """
    return udn_crawler.get_headline(search_term, (1, 10) if is_initial else 1)

def fetch_latest_news(is_initial=False):
    """
    get new info

    :param is_initial:
    :return:
    """
    news_data = fetch_latest_news_info("價格", is_initial=is_initial)
    for news in news_data:
        title = news.title
        relevance_judge_prompt = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "users", "content": f"{title}"},
        ]
        relevance = llm_generate(relevance_judge_prompt)
        if relevance == "high":
            detailed_news = udn_crawler.validate_and_parse(news.url)

            summarizer_prompt = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "users", "content": " ".join(detailed_news["content"])},
            ]

            result = llm_generate(summarizer_prompt)
            result = json.loads(result)
            detailed_news = NewsWithSummary(
                url=detailed_news.url,
                title=detailed_news.title,
                time=detailed_news.time,
                content=detailed_news.content,
                summary=result["影響"],
                reason=result["原因"],
            )
            import_news(detailed_news)

def fetch_news_upvote_details(news_id, user_id, db):
    count = (
        db.query(user_news_association_table)
        .filter_by(news_articles_id=news_id)
        .count()
    )
    voted = False
    if user_id:
        voted = (
                db.query(user_news_association_table)
                .filter_by(news_articles_id=news_id, user_id=user_id)
                .first()
                is not None
        )
    return count, voted

def toggle_upvote(news_id, user_id, db):
    existing_upvote = db.execute(
        select(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
    ).scalar()

    if existing_upvote:
        delete_command = delete(user_news_association_table).where(
            user_news_association_table.c.news_articles_id == news_id,
            user_news_association_table.c.user_id == user_id,
        )
        db.execute(delete_command)
        db.commit()
        return "Upvote removed"
    else:
        insert_command = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        db.execute(insert_command)
        db.commit()
        return "Article upvoted"

def news_exists(news_id, db: Session):
    return db.query(NewsArticle).filter_by(id=news_id).first() is not None
