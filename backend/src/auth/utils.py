from datetime import datetime, timedelta
from jose import jwt
from typing import Union
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from ..models import User
from ..config import Config

from .constants import DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=Config.Auth.TOKEN_ENTRY_URL)

def verify_password(secret, hashed_secret) -> bool:
    return password_context.verify(secret, hashed_secret)

def check_user_password_is_correct(db, username, password) -> Union[User, bool]:
    userdata = db.query(User).filter(User.username == username).first()
    if not verify_password(password, userdata.hashed_password):
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
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, Config.Auth.SECRET_KEY, algorithm="HS256")
    return encoded_jwt