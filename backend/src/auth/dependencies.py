from sqlalchemy.orm import Session
from fastapi import Depends
from jose import jwt

from ..database import db_engine
from ..models import User
from ..config import Config

from ..auth.utils import oauth2_scheme

def session_opener():
    session = Session(bind=db_engine)
    try:
        yield session
    finally:
        session.close()

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    db = Depends(session_opener)
):
    payload = jwt.decode(token, Config.Auth.SECRET_KEY, algorithms=["HS256"])
    return db.query(User).filter(User.username == payload.get("sub")).first()