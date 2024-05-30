# -*- coding: utf-8 -*-
# @Time : 2024/5/21  14:08
# @Author : Andy Hsieh
# @Desc :
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from aioredis import Redis, ConnectionPool
from settings import MONGOURI, REDISURI


async def mongoClient() -> AsyncIOMotorDatabase:
    try:
        client = AsyncIOMotorClient(MONGOURI)
        # client = AsyncIOMotorClient('mongodb://192.168.10.67:27017')
        db = client.finance
        yield db
    finally:
        pass


async def redisClient() -> Redis:
    try:
        cache_pool = ConnectionPool.from_url(
            url=REDISURI,
            decode_responses=True
        )
        # cache_pool = ConnectionPool.from_url(
        #     url='redis://192.168.10.67:6379/15',
        #     decode_responses=True
        # )
        cache = Redis(connection_pool=cache_pool)
        yield cache
    except:
        pass