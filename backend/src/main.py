from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from .database import db_engine
from .models import NewsArticle
from .services import background_scheduler
from .config import Config

from .news.utils import fetch_latest_news
from .news.router import router as news_router
from .users.router import router as users_router
from .prices.router import router as prices_router

app = FastAPI()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

app.include_router(news_router, prefix=Config.Basic.FASTAPI_PREFIX)
app.include_router(users_router, prefix=Config.Basic.FASTAPI_PREFIX)
app.include_router(prices_router, prefix=Config.Basic.FASTAPI_PREFIX)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=Config.Basic.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def start_scheduler():
    db = SessionLocal()
    if db.query(NewsArticle).count() == 0:
        # should change into simple factory pattern
        fetch_latest_news()
    db.close()
    background_scheduler.add_job(fetch_latest_news, "interval", minutes=Config.News.NEWS_FETCH_INTERVAL_MINUTES)
    background_scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()
