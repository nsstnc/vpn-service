import datetime
from typing import Optional, List

from fastapi.params import Query

from database import Base
import enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, MetaData, ForeignKey, Date, Enum

metadata = MetaData()


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    name: str
    password: str


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)



from pydantic import BaseModel



