import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from .config import Config
from .database import db_engine

sentry_sdk.init(
    dsn=Config.Basic.SENTRY_DSN,
    traces_sample_rate=Config.Basic.SENTRY_TRACES_SAMPLE_RATE,
    profiles_sample_rate=Config.Basic.SENTRY_PROFILES_SAMPLE_RATE,
)

sessionmaker(bind=db_engine)

background_scheduler = BackgroundScheduler()