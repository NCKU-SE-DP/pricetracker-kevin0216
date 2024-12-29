from .utils import init_logger
import logging
init_logger()

logging.debug("Initialisation started.")

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from .database import db_engine
from .models import NewsArticle
from .services import background_scheduler
from .config import Config

from .news.services import fetch_latest_news
from .news.router import router as news_router
from .users.router import router as users_router
from .prices.router import router as prices_router

app = FastAPI()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

app.include_router(news_router, prefix=Config.Basic.FASTAPI_PREFIX)
logging.debug("News router (/news) initialised")
app.include_router(users_router, prefix=Config.Basic.FASTAPI_PREFIX)
logging.debug("Users router (/router) initialised")
app.include_router(prices_router, prefix=Config.Basic.FASTAPI_PREFIX)
logging.debug("Prices router (/prices) initialised")

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
        logging.info("No news present in the database. Fetching latest news.")
        fetch_latest_news()
    db.close()
    background_scheduler.add_job(fetch_latest_news, "interval", minutes=Config.News.NEWS_FETCH_INTERVAL_MINUTES)
    background_scheduler.start()
    logging.debug("Background scheduler started.")
    logging.info("PriceTracker backend has started.")

@app.on_event("shutdown")
def shutdown_scheduler():
    background_scheduler.shutdown()
    logging.debug("Background scheduler shutdown.")
