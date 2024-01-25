from pydantic import BaseModel
from typing import Optional, List


class CompanyModel(BaseModel):
    nickname: str
    stock_id: str
    state: Optional[str] = ''
    plot: Optional[str] = ''
    employees: Optional[int] = 0


class GroupBody(BaseModel):
    title: str


class GroupListBody(BaseModel):
    stock_id: str
    stock_nickname: str
    groups: List


class NewsTaskBody(BaseModel):
    uid: str


class NoteBody(BaseModel):
    note: str
    stock_id: str