from fastapi import APIRouter, Depends
import json

from ..auth.dependencies import session_opener, authenticate_user_token
from ..utils import _id_counter

from .utils import toggle_upvote, fetch_news_upvote_details, fetch_latest_news_info, udn_crawler, anthropic_client
from ..models import NewsArticle
from .schema import PromptRequest, NewsSummaryRequestSchema, NewsSummaryCustomModelRequestSchema
from .utils import openai_client

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

@router.post("/{news_id}/upvote")
def upvote_article(
        news_id,
        db=Depends(session_opener),
        user=Depends(authenticate_user_token),
):
    message = toggle_upvote(news_id, user.id, db)
    return {"message": message}

@router.get("/news")
def fetch_news(db=Depends(session_opener)):
    """
    fetching all available news

    :param db: Database (Depends Session)
    :return List[Dict[str, bool]]: List of news
    """
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for news_item in news:
        upvote_num, is_upvoted = fetch_news_upvote_details(news_item.id, None, db)
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
    news = db.query(NewsArticle).order_by(NewsArticle.time.desc()).all()
    result = []
    for article in news:
        upvote_num, is_upvoted = fetch_news_upvote_details(article.id, user.id, db)
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
    prompt = request.prompt
    news_list = []

    keywords = openai_client.extract_search_keywords(prompt)
    # should change into simple factory pattern
    news_items = fetch_latest_news_info(keywords)
    for news in news_items:
        try:
            detailed_news = udn_crawler.validate_and_parse(news.url)

            detailed_news.id = next(_id_counter)
            news_list.append(detailed_news)
        except Exception as exception:
            print(exception)
    return sorted(news_list, key=lambda x: x.time, reverse=True)

@router.post("/news_summary")
async def news_summary(
        payload: NewsSummaryRequestSchema, user=Depends(authenticate_user_token)
):
    response = {}

    result = openai_client.generate_summary(payload.content)
    if result:
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response

@router.post("/news_summary_custom_model")
async def news_summary_with_custom_model(
        payload: NewsSummaryCustomModelRequestSchema, user=Depends(authenticate_user_token)
):
    response = {}

    if not payload.llm_model:
        return {"message": "Model is required."}
    elif payload.llm_model.lower() == "openai":
        result = openai_client.generate_summary(payload.content)
    elif payload.llm_model.lower() == "anthropic" or payload.llm_model.lower() == "claude":
        result = anthropic_client.generate_summary(payload.content)
    else:
        return {"message": "Invalid model."}

    if result:
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response