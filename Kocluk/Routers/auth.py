from datetime import timedelta, datetime, timezone
from urllib.request import Request
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr, constr
from typing import Annotated
from sqlalchemy import or_, func
import sqlalchemy.orm as Session
from starlette import status
from fastapi.security import  OAuth2PasswordRequestForm, OAuth2PasswordBearer, oauth2
from database import SessionLocal
from models import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")

class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=128)
    email: EmailStr
    first_Name: str
    last_Name: str
    password: str
    is_admin: bool

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(username:str, user_id: int, admin: bool, expires_delta:timedelta):
    payload = {'sub': username, 'id': user_id, 'admin': admin}
    expires = datetime.now(timezone.utc) + expires_delta
    payload.update({'exp': expires})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(login: str, password: str, db):
    user = db.query(User).filter(or_(User.username == login,func.lower(User.email) == login.lower())).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")

async def admin_get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        is_admin: bool = payload.get('admin')
        if username is None or user_id is None or is_admin is False:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        return {'username': username, 'id': user_id, 'is_admin': is_admin}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")

async def get_user_identifier(token: Annotated[str, Depends(oauth2_bearer)]):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get('id')
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not authenticated")
    return user_id

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    user = User(
        username=create_user_request.username,
        email=create_user_request.email.lower(),
        first_name=create_user_request.first_Name,
        last_name=create_user_request.last_Name,
        is_admin=create_user_request.is_admin,
        hashed_password=bcrypt_context.hash(create_user_request.password)
    )
    db.add(user)
    db.commit()

@router.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(user.username, user.id, user.is_admin, timedelta(minutes=60))
    return {'access_token': token, 'token_type': 'bearer'}