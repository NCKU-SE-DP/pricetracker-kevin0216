from fastapi import APIRouter, Depends
import json

from ..auth.dependencies import session_opener, authenticate_user_token
from ..utils import _id_counter, llm_generate

from .utils import toggle_upvote, fetch_news_upvote_details, fetch_latest_news_info, udn_crawler
from ..models import NewsArticle
from .schema import PromptRequest, NewsSummaryRequestSchema

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
    extract_keyword_prompt = [
        {
            "role": "system",
            "content": "你是一個關鍵字提取機器人，用戶將會輸入一段文字，表示其希望看見的新聞內容，請提取出用戶希望看見的關鍵字，請截取最重要的關鍵字即可，避免出現「新聞」、「資訊」等混淆搜尋引擎的字詞。(僅須回答關鍵字，若有多個關鍵字，請以空格分隔)",
        },
        {"role": "users", "content": f"{prompt}"},
    ]

    keywords = llm_generate(extract_keyword_prompt)
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
    summarizer_prompt = [
        {
            "role": "system",
            "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
        },
        {"role": "users", "content": f"{payload.content}"},
    ]

    result = llm_generate(summarizer_prompt)
    if result:
        result = json.loads(result)
        response["summary"] = result["影響"]
        response["reason"] = result["原因"]
    return response