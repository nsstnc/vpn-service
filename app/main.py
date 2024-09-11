from fastapi import FastAPI, Query, Form, status, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import importlib
from fastapi import HTTPException, Depends
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from database import Base, engine, init_db, get_session

from app.routers.login import router as login_router
from config import AUTH_SECRET
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
app = FastAPI(
    title="facebook-advertising-campaigns",
)

app.add_middleware(SessionMiddleware, secret_key=AUTH_SECRET)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(login_router)
app.mount("/styles", StaticFiles(directory="./src/styles"), name="styles")


if __name__ == "__main__":

    init_db()
    try:
        connection = engine.connect()
        print("Соединение с базой данных установлено")
        connection.close()
    except Exception as e:
        print(f"Ошибка соединения с базой данных: {e}")

    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

