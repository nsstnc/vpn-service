import json
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi import FastAPI, Query, Form, status, Request, Response
from fastapi.responses import HTMLResponse
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import insert, select, update, delete
from sqlalchemy.orm import Session
from app.database import get_session
from app.models import *
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from app.config import AUTH_SECRET
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.responses import RedirectResponse
from fastapi_login.exceptions import InvalidCredentialsException
import requests

router = APIRouter(
    prefix="",
    tags=["auth"]
)

manager = LoginManager(AUTH_SECRET, token_url="/auth/login", use_cookie=True, default_expiry=timedelta(hours=24))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="src")


@manager.user_loader(get_session)
def get_user(email: str, get_session):
    db = next(get_session())
    user = db.query(Users).filter(Users.email == email).first()
    return user


@router.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_session)):
    user = get_user(email, get_session)
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    access_token = manager.create_access_token(data={"sub": email})
    if user.status == Status.ADMIN:
        redirect_response = RedirectResponse(url="/admin", status_code=303)
    else:
        redirect_response = RedirectResponse(url="/main", status_code=302)
    manager.set_cookie(redirect_response, access_token)

    return redirect_response
    # return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def register(request: Request, email: str = Form(...), name: str = Form(...), password: str = Form(...),
             db: Session = Depends(get_session)):
    user = db.query(Users).filter(Users.email == email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Такой email уже зарегистрирован"
        )
    hashed_password = pwd_context.hash(password)
    new_user = Users(email=email, name=name, password=hashed_password, status=Status.ADMIN)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return templates.TemplateResponse(request=request, name="login.html",
                                      context={"message": "Пользователь зарегистрирован"})
    # return {"message": "Пользователь создан и зарегистрирован"}


@router.get("/main")
def main_protected(request: Request, user=Depends(manager), db: Session = Depends(get_session)):
    return templates.TemplateResponse(request=request, name="main.html",
                                      context={"name": user.name})





@router.get("/", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/logout")
def logout(request: Request):
    # request.session.clear()
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access-token")
    return response
