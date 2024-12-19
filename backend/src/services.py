import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import sessionmaker

from .config import Config
from .database import db_engine

sentry_sdk.init(
    dsn=Config.Basic.SENTRY_DSN,
    traces_sample_rate=Config.Basic.SENTRY_TRACES_SAMPLE_RATE,
    profiles_sample_rate=Config.Basic.SENTRY_PROFILES_SAMPLE_RATE,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)

sessionmaker(bind=db_engine)

background_scheduler = BackgroundScheduler()