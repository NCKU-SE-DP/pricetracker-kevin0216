from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session

from ..config import Config
from ..auth.dependencies import session_opener, authenticate_user_token
from ..auth.utils import check_user_password_is_correct, create_access_token, password_context

from ..models import User
from .schema import UserAuthSchema

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(session_opener)
):
    """login"""
    user = check_user_password_is_correct(db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, valid_duration=timedelta(minutes=Config.Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
def create_user(user: UserAuthSchema, db: Session = Depends(session_opener)):
    """create users"""
    hashed_password = password_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me")
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}