from sqlalchemy.orm import Session
from fastapi import Depends
from jose import jwt
from fastapi.security import OAuth2PasswordBearer

from ..database import db_engine
from ..models import User
from ..config import Config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=Config.Auth.TOKEN_ENTRY_URL)

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