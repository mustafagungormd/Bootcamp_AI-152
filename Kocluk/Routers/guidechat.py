from fastapi import APIRouter, Body, Path, Query, HTTPException, Depends, Request
from sqlalchemy.testing.suite.test_reflection import users
from starlette.responses import RedirectResponse
from models import Base, User, Chat, Technique
from database import engine, SessionLocal
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from starlette import status
from pydantic import BaseModel, Field
import os
from AI.aimodel import Gemini
from Routers.throttling import apply_rate_limit
from Routers.auth import get_user_identifier, get_current_user
from dotenv import load_dotenv
import re

load_dotenv()

router = APIRouter(
    prefix="/guide_chat",
    tags=["chat"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response


# --- AI Configuration ---
def load_system_prompt():
    try:
        with open("Routers/Prompts/guide.md", "r") as f:
            return f.read()
    except FileNotFoundError:
        return None


system_prompt = load_system_prompt()
gemini_api_key = os.getenv("API_KEY")

ai_platform = Gemini(api_key=gemini_api_key, system_prompt=system_prompt)


class ChatRequest(BaseModel):
    title: str
    body_text: str


class ChatResponse(BaseModel):
    response: str



TECHNIQUE_RE = re.compile(r'^ *Technique:\s*(.+)$', flags=re.MULTILINE)

TIME_RE_MINUTES = re.compile(
    r'^ *Time:\s*(\d+)\s*(?:min(?:ute)?s?)?$',
    flags=re.MULTILINE | re.IGNORECASE
)

EXPLANATION_RE = re.compile(r'^ *Explanation:\s*(.+)$', flags=re.MULTILINE)

BODY_TEXT_RE = re.compile(r'^ *Body Text:\s*(.+)$', flags=re.MULTILINE)

TITLE_RE = re.compile(r'^ *Title:\s*(.+)$', flags=re.MULTILINE)


async def technique_get(data: str):
    technique = TECHNIQUE_RE.findall(data)
    return technique

async def time_get(data: str):
    time = TIME_RE_MINUTES.findall(data)
    return time

async def explanation_get(data: str):
    explanation = EXPLANATION_RE.findall(data)
    return explanation

async def body_text_get(data: str):
    body_text = BODY_TEXT_RE.search(data)
    return body_text

async def title_get(data: str) :
    title = TITLE_RE.search(data)
    return title

@router.get("/")
async def render_chat_bar(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        chat = db.query(Chat).filter(Chat.owner_id == user.get('id')).all()
        return chat
    except:
        return redirect_to_login()


@router.post("/", response_model=ChatResponse)
async def create_chat_request(user: user_dependency, db: db_dependency, chat_request: ChatRequest,
                              user_id: int = Depends(get_user_identifier)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    apply_rate_limit(user_id)
    response_text = ai_platform.chat(chat_request.prompt)

    time_text = await time_get(response_text)
    technique_text = await technique_get(response_text)
    explanation_text = await explanation_get(response_text)

    body_text = await body_text_get(response_text)
    title_text = await title_get(response_text)

    if not (len(technique_text) == len(time_text) == len(explanation_text)):
        raise HTTPException(500, "Parser returned mismatched lengths")

    chat = Chat(
        chat_title=title_text.group(1),
        body_text=body_text.group(1),
        owner_id=user.id,
    )

    # attach children AFTER creation (or use techniques=[...] here)
    chat.techniques = [
        Technique(technique=n, time=int(t), explanation=e)
        for n, t, e in zip(technique_text, time_text, explanation_text)
    ]

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return ChatResponse(response=response_text)



@router.get("/root")
async def root():
    return {"message": "API is running "}
