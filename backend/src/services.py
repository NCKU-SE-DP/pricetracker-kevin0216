import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler

from .config import Config

sentry_sdk.init(
    dsn=Config.Basic.SENTRY_DSN,
    traces_sample_rate=Config.Basic.SENTRY_TRACES_SAMPLE_RATE,
    profiles_sample_rate=Config.Basic.SENTRY_PROFILES_SAMPLE_RATE,
)

background_scheduler = BackgroundScheduler()