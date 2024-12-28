from sqlalchemy import select, delete, insert
from sqlalchemy.orm import Session

from .exceptions import UpvoteException
from ..config import Config
from ..crawler.crawler_base import NewsWithSummary
from ..crawler.udn_crawler import UDNCrawler
from ..llm_client.anthropic_client import AnthropicClient
from ..llm_client.base import RelevanceEvaluation
from ..llm_client.exceptions import EvaluationFailure
from ..llm_client.openai_client import OpenAIClient
from ..models import user_news_association_table
from ..utils import log_exception, ExceptionLevel

udn_crawler = UDNCrawler()
openai_client = OpenAIClient(api_key=Config.OpenAI.OPENAI_TOKEN)
anthropic_client = AnthropicClient(api_key=Config.Anthropic.ANTHROPIC_TOKEN)


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
    return udn_crawler.startup(search_term) if is_initial else udn_crawler.get_headlines(search_term, 1)


def fetch_latest_news(is_initial=False):
    """
    get new info

    :param is_initial:
    :return:
    """
    news_data = fetch_latest_news_info("價格", is_initial=is_initial)
    for news in news_data:
        title = news.title
        try:
            relevance = openai_client.evaluate_relevance(title, "民生用品的價格變化")
        except EvaluationFailure as e:
            log_exception(e, ExceptionLevel.WARNING, f"Failed to evaluate relevance for news {title}")
            return
        if relevance == RelevanceEvaluation.HIGH:
            try:
                detailed_news = udn_crawler.validate_and_parse(news.url)
            except Exception as e:
                log_exception(e, ExceptionLevel.WARNING, f"Failed to validate and parse news for {news.title}")
                continue

            if detailed_news is None:
                continue

            try:
                result = openai_client.generate_summary(" ".join(detailed_news.content))
            except EvaluationFailure as e:
                log_exception(e, ExceptionLevel.WARNING, f"Failed to generate summary for news {news.title}")
                continue
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
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise UpvoteException("Failed to remove upvote")
        return "Upvote removed"
    else:
        insert_command = insert(user_news_association_table).values(
            news_articles_id=news_id, user_id=user_id
        )
        db.execute(insert_command)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise UpvoteException("Failed to upvote")
        return "Article upvoted"
