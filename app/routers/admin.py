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
from app.routers.login import manager, get_user
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.responses import RedirectResponse
from fastapi_login.exceptions import InvalidCredentialsException
import requests

router = APIRouter(
    prefix="",
    tags=["admin"]
)

templates = Jinja2Templates(directory="src")


@router.get("/admin")
def main_protected(request: Request, user=Depends(manager), db: Session = Depends(get_session)):
    if user.status != Status.ADMIN:
        return RedirectResponse(url="/main", status_code=302)
    return templates.TemplateResponse(request=request, name="admin.html",
                                      context={"name": user.name})


@router.get("/admin/accounts")
def main_protected(request: Request, user=Depends(manager), db: Session = Depends(get_session)):
    if user.status != Status.ADMIN:
        return RedirectResponse(url="/main", status_code=302)
    return templates.TemplateResponse(request=request, name="admin_accounts.html",
                                      context={"name": user.name})


@router.get("/admin/servers")
def main_protected(request: Request, user=Depends(manager), db: Session = Depends(get_session)):
    if user.status != Status.ADMIN:
        return RedirectResponse(url="/main", status_code=302)
    return templates.TemplateResponse(request=request, name="admin_servers.html",
                                      context={"name": user.name})
