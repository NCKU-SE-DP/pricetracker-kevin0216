from sqlalchemy.orm import Session

from ..models import NewsArticle

def news_exists(news_id, db: Session):
    return db.query(NewsArticle).filter_by(id=news_id).first() is not None
