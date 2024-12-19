from sqlalchemy.orm import Session
from fastapi import Depends
import logging
from fastapi import HTTPException
from sentry_sdk import capture_exception
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
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
    try:
        logging.debug(f"Authenticating token: {token[:10]}...")
        payload = jwt.decode(token, Config.Auth.SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError as e:
        logging.error(f"Token expired: {e}")
        capture_exception(e)
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        logging.error(f"Token invalid: {e}")
        capture_exception(e)
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logging.error(f"Failed to authenticate token: {e}")
        capture_exception(e)
        raise HTTPException(status_code=401, detail="Failed to authenticate token")
    return db.query(User).filter(User.username == payload.get("sub")).first()