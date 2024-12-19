from datetime import datetime, timedelta
from jose import jwt
from typing import Union
from passlib.context import CryptContext
import logging
from sentry_sdk import capture_exception

from ..models import User
from ..config import Config

from .constants import DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(secret, hashed_secret) -> bool:
    return password_context.verify(secret, hashed_secret)

def check_user_password_is_correct(db, username, password) -> Union[User, bool]:
    userdata = db.query(User).filter(User.username == username).first()
    if userdata is None:
        logging.debug(f"User not found: {username}")
        return False
    try:
        if not verify_password(password, userdata.hashed_password):
            logging.debug(f"Password is incorrect for user: {username}")
            return False
    except Exception as e:
        logging.error(f"Failed to verify password: {e}")
        capture_exception(e)
        return False
    return userdata

def create_access_token(data, valid_duration=None) -> str:
    """create access token"""
    to_encode = data.copy()
    if valid_duration:
        expire = datetime.utcnow() + valid_duration
    else:
        expire = datetime.utcnow() + timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, Config.Auth.SECRET_KEY, algorithm="HS256")
    except Exception as e:
        logging.error(f"Error while encoding with jwt: {e}")
        raise e
    return encoded_jwt