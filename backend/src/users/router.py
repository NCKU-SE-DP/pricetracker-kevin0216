from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session
from sentry_sdk import capture_exception
import logging

from ..config import Config
from ..auth.dependencies import session_opener, authenticate_user_token
from ..auth.utils import check_user_password_is_correct, create_access_token, password_context

from ..models import User
from .schema import UserAuthSchema
from ..utils import log_exception, ExceptionLevel

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={418: {"description": "I'm a teapot, I can't brew coffee"}},
)

@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(session_opener)
):
    """login"""
    logging.debug(f"Login initialised: {form_data.username}")
    user = check_user_password_is_correct(db, form_data.username, form_data.password)
    if not user:
        logging.debug(f"Failed to login: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    try:
        access_token = create_access_token(
            data={"sub": str(user.username)}, valid_duration=timedelta(minutes=Config.Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    except Exception as e:
        capture_exception(e)
        raise HTTPException(status_code=400, detail="Something went wrong while processing the request")
    logging.debug(f"Logged in: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def create_user(user: UserAuthSchema, db: Session = Depends(session_opener)):
    """create users"""
    logging.debug(f"Creating user: {user.username}")
    if len(user.username) > Config.Auth.USERNAME_MAX_LENGTH:
        logging.debug(f"Username too long: {user.username}")
        raise HTTPException(status_code=418, detail="Username format is not accepted")
    hashed_password = password_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    try:
        db.commit()
    except Exception as e:
        log_exception(e, ExceptionLevel.WARNING, "Failed to create user")
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create user")
    db.refresh(db_user)
    logging.debug(f"Created user: {user.username}")
    return db_user

@router.get("/me")
def read_users_me(user=Depends(authenticate_user_token)):
    logging.debug(f"Accessed /api/v1/users/me: {user.username}")
    return {"username": user.username}