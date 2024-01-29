# -*- coding: utf-8 -*-
# @Time : 2023/12/28  下午 12:27
# @Author : Andy Hsieh
# @Desc :
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from aioredis import Redis, ConnectionPool


async def mongo_connector() -> AsyncIOMotorDatabase:
    try:
        # client = AsyncIOMotorClient('mongodb://andy.h:123456@127.0.0.1:27017')
        client = AsyncIOMotorClient('mongodb://192.168.10.67:27017')
        db = client.finance
        yield db
    finally:
        pass


async def redis_cache() -> Redis:
    try:
        # cache_pool = ConnectionPool.from_url(
        #     url='redis://127.0.0.1:6379/15',
        #     decode_responses=True
        # )
        cache_pool = ConnectionPool.from_url(
            url='redis://192.168.10.67:6379/15',
            decode_responses=True
        )
        cache = Redis(connection_pool=cache_pool)
        yield cache
    except:
        pass