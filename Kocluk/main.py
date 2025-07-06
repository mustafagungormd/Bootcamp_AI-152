from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse
from models import Base
from database import engine
from starlette import status
from Routers.auth import router as auth_router
from Routers.guidechat import router as guidechat_router
from dotenv import load_dotenv

app = FastAPI()

def configure():
    load_dotenv()

@app.get("/")
def read_root(request: Request):
    return RedirectResponse(url="/*", status_code=status.HTTP_302_FOUND)


app.include_router(auth_router)

app.include_router(guidechat_router)

Base.metadata.create_all(bind=engine)