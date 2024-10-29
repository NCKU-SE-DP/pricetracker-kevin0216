from urllib.parse import quote
import requests
import json
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from ..models import user_news_association_table
from ..utils import llm_generate

from ..models import NewsArticle


def extract_news(news):
    response = requests.get(news["titleLink"])
    soup = BeautifulSoup(response.text, "html.parser")
    # 標題
    title = soup.find("h1", class_="article-content__title").text
    content_time = soup.find("time", class_="article-content__time").text
    # 定位到包含文章内容的 <section>
    content_section = soup.find("section", class_="article-content__editor")

    paragraphs = [
        paragraph.text
        for paragraph in content_section.find_all("p")
        if paragraph.text.strip() != "" and "▪" not in paragraph.text
    ]
    detailed_news = {
        "url": news["titleLink"],
        "title": title,
        "time": content_time,
        "content": paragraphs,
    }

    return detailed_news

def import_news(news_data):
    """
    add new to db
    :param news_data: news info
    :return:
    """
    session = Session()
    session.add(NewsArticle(
        url=news_data["url"],
        title=news_data["title"],
        time=news_data["time"],
        content=" ".join(news_data["content"]),  # 將內容list轉換為字串
        summary=news_data["summary"],
        reason=news_data["reason"],
    ))
    session.commit()
    session.close()


def fetch_latest_news_info(search_term, is_initial=False):
    """
    get new

    :param search_term:
    :param is_initial:
    :return:
    """
    all_news_data = []
    # iterate pages to get more news data, not actually get all news data
    if is_initial:
        news_data = []
        for page in range(1, 10):
            page_metadata = {
                "page": page,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get("https://udn.com/api/more", params=page_metadata)
            news_data.append(response.json()["lists"])

        for news_list in news_data:
            all_news_data.append(news_list)
    else:
        page_metadata = {
            "page": 1,
            "id": f"search:{quote(search_term)}",
            "channelId": 2,
            "type": "searchword",
        }
        response = requests.get("https://udn.com/api/more", params=page_metadata)

        all_news_data = response.json()["lists"]
    return all_news_data

def fetch_latest_news(is_initial=False):
    """
    get new info

    :param is_initial:
    :return:
    """
    news_data = fetch_latest_news_info("價格", is_initial=is_initial)
    for news in news_data:
        title = news["title"]
        relevance_judge_prompt = [
            {
                "role": "system",
                "content": "你是一個關聯度評估機器人，請評估新聞標題是否與「民生用品的價格變化」相關，並給予'high'、'medium'、'low'評價。(僅需回答'high'、'medium'、'low'三個詞之一)",
            },
            {"role": "users", "content": f"{title}"},
        ]
        relevance = llm_generate(relevance_judge_prompt)
        if relevance == "high":
            detailed_news = extract_news(news)

            summarizer_prompt = [
                {
                    "role": "system",
                    "content": "你是一個新聞摘要生成機器人，請統整新聞中提及的影響及主要原因 (影響、原因各50個字，請以json格式回答 {'影響': '...', '原因': '...'})",
                },
                {"role": "users", "content": " ".join(detailed_news["content"])},
            ]

            result = llm_generate(summarizer_prompt)
            result = json.loads(result)
            detailed_news["summary"] = result["影響"]
            detailed_news["reason"] = result["原因"]
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
