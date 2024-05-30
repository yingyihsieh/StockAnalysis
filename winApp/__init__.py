# -*- coding: utf-8 -*-
# @Time : 2024/5/20  17:44
# @Author : Andy Hsieh
# @Desc :



import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from winApi.common import common_router
from winApi.tw import tw_router
from winApi.cn import cn_router
from settings import STATIC_PATH


def register_cors(app: FastAPI):
    """跨域初始化"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


def register_router(app: FastAPI):
    app.include_router(common_router)
    app.include_router(tw_router, prefix='/tw')
    app.include_router(cn_router, prefix='/cn')


def create_app():
    server = FastAPI()
    if not os.path.exists(STATIC_PATH):
        os.mkdir(STATIC_PATH)
    server.mount("/static", StaticFiles(directory="static"), name="static")
    register_cors(server)
    register_router(server)
    return server