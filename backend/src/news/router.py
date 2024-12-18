from fastapi import APIRouter, Depends, HTTPException
import itertools
import logging
from sentry_sdk import capture_exception
from typing import Union

from ..auth.dependencies import session_opener, authenticate_user_token

from .utils import toggle_upvote, fetch_news_upvote_details, fetch_latest_news_info, udn_crawler, openai_client, anthropic_client
from ..models import NewsArticle
from .schema import PromptRequest, NewsSummaryRequestSchema, NewsSummaryCustomModelRequestSchema
from ..llm_client.exceptions import EvaluationFailure
from ..crawler.exceptions import CrawlerException

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

_id_counter = itertools.count(start=1000000)

@router.post("/{news_id}/upvote")
def upvote_article(
        news_id,
        db=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    logging.debug(f"{user.id} accessed /api/v1/news/{news_id}/upvote")
    message = toggle_upvote(news_id, user.id, db)
    return {"message": message}

@router.get("/news")
def fetch_news(db=Depends(session_opener)):
    """
    fetching all available news

    :param db: Database (Depends Session)
    :return List[Dict[str, bool]]: List of news
    """
    logging.debug("Accessed /api/v1/news/news")
    try:
        news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except Exception as e:
        logging.error(f"Failed to fetch news: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Failed to fetch news")
    result = []
    for news_item in news:
        try:
            upvote_num, is_upvoted = fetch_news_upvote_details(news_item.id, None, db)
        except Exception as e:
            logging.warning(f"Failed to fetch upvote details for news '{news_item.id}': {e}, skipping.")
            capture_exception(e)
            continue
        result.append(
            {**news_item.__dict__, "upvotes": upvote_num, "is_upvoted": is_upvoted}
        )
    return result

@router.get("/user_news")
def fetch_user_upvoted_news(
        db=Depends(session_opener),
        user=Depends(authenticate_user_token)
):
    """
    fetching all news upvoted by user

    :param db: Database (Depends Session)
    :param user: User (Depends authenticate_user_token)
    :return List[Dict[str, bool]]: List of news
    """
    logging.debug(f"{user.id} accessed /api/v1/news/user_news")
    try:
        news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    except Exception as e:
        logging.error(f"Failed to fetch news: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Failed to fetch news")
    result = []
    for article in news:
        try:
            upvote_num, is_upvoted = fetch_news_upvote_details(article.id, user.id, db)
        except Exception as e:
            logging.warning(f"Failed to fetch upvote details for news '{article.id}': {e}, skipping.")
            capture_exception(e)
            continue
        result.append(
            {
                **article.__dict__,
                "upvotes": upvote_num,
                "is_upvoted": is_upvoted,
            }
        )
    return result

@router.post("/search_news")
async def search_news(request: PromptRequest):
    logging.debug(f"Accessed /api/v1/news/search_news: {request.prompt}")
    prompt = request.prompt
    news_list = []

    try:
        keywords = openai_client.extract_search_keywords(prompt)
    except EvaluationFailure as e:
        logging.error(f"Failed to extract search keywords: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Something went wrong while processing search keywords")
    # should change into simple factory pattern
    try:
        news_items = fetch_latest_news_info(keywords)
    except Exception as e:
        logging.error(f"Failed to fetch news info: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Failed to fetch news info")
    for news in news_items:
        try:
            detailed_news = udn_crawler.validate_and_parse(news.url)
        except Exception as e:
            logging.error(f"Failed to validate and parse news: {e}")
            capture_exception(e)
            continue
        detailed_news.id = next(_id_counter)
        news_list.append(detailed_news)
    return sorted(news_list, key=lambda x: x.time, reverse=True)

async def _generate_summary(
        payload: Union[NewsSummaryRequestSchema, NewsSummaryCustomModelRequestSchema], user=Depends(authenticate_user_token), llm_model="openai"
):
    response = {}

    try:
        if not llm_model:
            return HTTPException(status_code=400, detail="Model is required")
        elif llm_model.lower() == "openai":
            result = openai_client.generate_summary(payload.content)
        elif llm_model.lower() == "anthropic" or llm_model.lower() == "claude":
            result = anthropic_client.generate_summary(payload.content)
        else:
            return HTTPException(status_code=400, detail="Invalid model")
    except EvaluationFailure as e:
        logging.error(f"Failed to generate summary: {e}")
        capture_exception(e)
        return HTTPException(status_code=400, detail="Failed to generate summary")

    if result:
        try:
            response["summary"] = result["影響"]
            response["reason"] = result["原因"]
        except KeyError as e:
            logging.error(f"Failed to extract summary and reason as format returned from LLM is incorrect: {e}")
            capture_exception(e)
            return HTTPException(status_code=400, detail="Something went wrong while processing summary")
    return response

@router.post("/news_summary")
async def news_summary(
        payload: NewsSummaryRequestSchema, user=Depends(authenticate_user_token)
):
    return await _generate_summary(payload, user)

@router.post("/news_summary_custom_model")
async def news_summary_with_custom_model(
        payload: NewsSummaryCustomModelRequestSchema, user=Depends(authenticate_user_token)
):
    return await _generate_summary(payload, user, payload.llm_model)