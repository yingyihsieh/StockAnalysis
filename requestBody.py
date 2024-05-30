# -*- coding: utf-8 -*-
# @Time : 2024/5/21  14:21
# @Author : Andy Hsieh
# @Desc :
from pydantic import BaseModel


class GroupBody(BaseModel):
    title: str


class NewsTaskBody(BaseModel):
    uid: str


class NoteBody(BaseModel):
    note: str
    stock_id: str


class EPSBody(BaseModel):
    stock_id: str
    eps: float
    per_1: float
    per_2: float
    per_3: float
    per1: float
    per2: float
    per3: float


class GroupItemBody(BaseModel):
    stock_id: str
    stock_nickname: str
    group_id: str
    group_name: str