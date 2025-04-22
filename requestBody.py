# -*- coding: utf-8 -*-
# @Time : 2024/5/21  14:21
# @Author : Andy Hsieh
# @Desc :
from pydantic import BaseModel
from typing import List

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


class FundBody(BaseModel):
    industry: list


class ShipBody(BaseModel):
    row_data: List[List[int]]
    quantity: int
    weight: int


class CompareBody(BaseModel):
    row_data: List[List[str]]


class DimensionRequest(BaseModel):
    min_length: int
    max_length: int
    min_width: int
    max_width: int
    min_height: int
    max_height: int