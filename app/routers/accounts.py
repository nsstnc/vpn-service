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
from app.config import AUTH_SECRET, SMTP_EMAIL, SMTP_PASSWORD
from app.routers.login import manager, get_user
from app.utils.EmailSender import EmailSender
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.responses import RedirectResponse
from fastapi_login.exceptions import InvalidCredentialsException
import requests
import random
import string


router = APIRouter(
    prefix="",
    tags=["accounts"]
)

templates = Jinja2Templates(directory="src")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


email_sender = EmailSender(SMTP_EMAIL, SMTP_PASSWORD)

def generate_password(length=8, include_symbols=True):
    """Генерирует случайный пароль.

    :param length: Длина пароля.
    :param include_symbols: Включать ли специальные символы.
    :return: Сгенерированный пароль.
    """
    characters = string.ascii_letters + string.digits
    if include_symbols:
        characters += string.punctuation

    return ''.join(random.choice(characters) for _ in range(length))


@router.post("/accounts/register")
def register(request: Request, email: str = Form(...), name: str = Form(...),
             user=Depends(manager),
             db: Session = Depends(get_session)):
    if user.status != Status.ADMIN:
        return RedirectResponse(url="/main", status_code=302)

    email_exists = db.query(Users).filter(Users.email == email).first()
    if email_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Такой email уже зарегистрирован"
        )

    password = generate_password()
    hashed_password = pwd_context.hash(password)
    new_user = Users(email=email, name=name, password=hashed_password, status=Status.USER)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    email_sender.send_email("Регистрация аккаунта",
                            (f"Здравствуйте, {name}!\n\n"
                             f"Ваш аккаунт на vpn-service успешно зарегистрирован администратором.\n\n"
                             f"Данные для входа:\n"
                             f"Логин: {email}\n"
                             f"Пароль: {password}\n"),
                            email)

    return templates.TemplateResponse(request=request, name="admin_accounts.html",
                                      context={"message": "Пользователь зарегистрирован",
                                               "current_page": "admin"})
    # return {"message": "Пользователь создан и зарегистрирован"}
