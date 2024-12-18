from sqlalchemy import create_engine

from .models import Base

db_engine = create_engine("sqlite:///news_database.db", echo=True)

Base.metadata.create_all(db_engine)