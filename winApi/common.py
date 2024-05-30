# -*- coding: utf-8 -*-
# @Time : 2024/5/22  11:42
# @Author : Andy Hsieh
# @Desc :
import asyncio

import pendulum
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from fastapi.requests import Request
from sse_starlette.sse import EventSourceResponse
from settings import msg_content
from utils.func import tsFormat
from utils.task import world_finance_task, income_task
from database import mongoClient
from charts.common import usd2nt_Line



common_router = APIRouter()
templates = Jinja2Templates(directory='templates')


async def message_generator(request):
    while True:
        content = msg_content.content

        if not await request.is_disconnected():
            if content:
                print('message = ', content)
                yield {
                    "event": "message",
                    "retry": 30000,
                    "data": content
                }
                msg_content.content = ''
            else:

                yield {
                    "event": "message",
                    "retry": 30000,
                    "data": ''
                }
        await asyncio.sleep(1)


@common_router.get('/')
async def home(request: Request):
    return templates.TemplateResponse(
        'demo_home.html',
        {
            'request': request,
        },
    )


@common_router.get('/test')
async def test_html(request: Request):
    return templates.TemplateResponse(
        'test_groups.html',
        {
            'request': request,
        },
    )


@common_router.get('/group_admin')
async def group_admin(request: Request,
                      db=Depends(mongoClient)):
    twlookup = {
        '$lookup':
            {
                "from": "group_news",  # 需要联合查询的另一张表B
                "localField": "uid",  # 表A的字段
                "foreignField": "group_id",  # 表B的字段
                "as": "group_docs"  # 根据A、B联合生成的新字段名
            },
    }
    cnlookup = {
        '$lookup':
            {
                "from": "cn_groupDetail",  # 需要联合查询的另一张表B
                "localField": "uid",  # 表A的字段
                "foreignField": "group_id",  # 表B的字段
                "as": "group_docs"  # 根据A、B联合生成的新字段名
            },
    }
    project = {
        '$project': {
            '_id': 0, 'group_docs._id': 0
        }
    }
    twdata = db.groups.aggregate([twlookup, project])
    cndata = db.cn_group.aggregate([cnlookup, project])
    twdataset = [d async for d in twdata]
    cndataset = [d async for d in cndata]
    print(twdataset)
    print(cndataset)
    return templates.TemplateResponse(
        'demo_group_admin.html',
        {
            'request': request,
            'twGroups': twdataset,
            'cnGroups': cndataset,
        },
    )


@common_router.get('/stock/world')
async def latest_world_finance(request: Request,
                               db=Depends(mongoClient)):
    model = db.world_stock
    queryset = model.find({}, {'_id': 0}).sort([('date', -1)]).limit(1)
    new_data = dict()
    async for q in queryset:
        new_data.update(q)
    date = tsFormat(new_data.get('date', pendulum.today(tz='Asia/Taipei').timestamp()) )

    return templates.TemplateResponse(
        'demo_wf.html',
        {
            'request': request,
            'data': new_data,
            'date': date,
            'keys': ['US10Y-Y', 'US10Y-Y△%', 'USIND', 'USIND△%', 'DJIA', 'DJIA△%', 'NASDAQ', 'NASDAQ△%', 'SOX',
                     'SOX△%', 'HSIND', 'HSIND△%', 'SSEC', 'SSEC△%', 'CSI300', 'CSI300△%',
                     'FI-NET', 'FI-Future-OI', 'FI-Option-OI', 'PC-R', 'US/NT', 'Top5Position',
                     'Top10Position', 'BullBearIND-R'],
        },
    )


@common_router.get("/notification")
async def notification(request: Request):
    event_generator = message_generator(request)
    return EventSourceResponse(event_generator)


@common_router.get('/signal/wft')
async def world_finance(
        task: BackgroundTasks,
):
    task.add_task(world_finance_task)
    return {'code': 1, 'data': None, 'msg': '成功'}


@common_router.get('/signal/income')
async def latest_income(
        task: BackgroundTasks,
):
    task.add_task(income_task)
    return {'code': 1, 'data': None, 'msg': '成功'}


@common_router.get('/usd2nt')
async def usd2nt_chart(db=Depends(mongoClient)):
    data = db.world_stock.find({},{'_id':0, 'US/NT':1, 'date':1}).sort([('date', -1)]).limit(1000)
    x_data, y_data = list(), list()
    async for d in data:
        x_data.insert(0, pendulum.from_timestamp(d['date'], tz='Asia/Taipei').format('YYYYMMDD'))
        y_data.insert(0, d['US/NT'])

    line = usd2nt_Line(x=x_data, y=y_data)
    return line.dump_options_with_quotes()


@common_router.get('/hotNews')
async def read_news(request: Request,
                    db=Depends(mongoClient)):
    tw_groups = db.groups.find({}, {'_id': 0})
    tw_groups = [t async for t in tw_groups]
    cn_groups = db.cn_group.find({}, {'_id': 0})
    cn_groups = [c async for c in cn_groups]
    return templates.TemplateResponse(
        'read_news.html',
        {
            'request': request,
            'tw_groups': tw_groups,
            'cn_groups': cn_groups
        },
    )


@common_router.get('/news/{loc}')
async def get_news_list(loc: str=Path(...),
                        group_id: str=Query(default=''),
                        db=Depends(mongoClient)):
    time_filter = {'$gte': pendulum.now(tz='Asia/Taipei').add(hours=-24)}
    project = {'_id': 0}
    if loc == 'tw':
        stocks = db.group_news.find({'group_id': group_id}, project)
        stocks = [s['stock_id'] async for s in stocks]
        data = db.news.find({"stock_id": {"$in": stocks}, 'created': time_filter}, project)
    elif loc == 'cn':
        stocks = db.cn_groupDetail.find({'group_id': group_id}, project)
        stocks = [s['stock_id'] async for s in stocks]
        data = db.cn_news.find({"stock_id": {"$in": stocks}, 'created': time_filter}, project)
    elif loc == 'nfsf':
        data = db.nfsf.find({'created': time_filter}, project)
    elif loc == 'cnsf':
        data = db.cnsf.find({'created': time_filter}, project)
    else:
        return {'code': 0, 'data': '', 'msg': '路徑錯誤'}

    news_list = list()
    async for d in data:
        d["created"] = pendulum.parse(str(d["created"]), tz='Asia/Taipei').format('YYYY-MM-DD HH:mm:ss')
        if loc in ['tw', 'cn']:
            html_str = f'<a href="{d["link"]}" class="list-group-item"><h4 class="list-group-item-heading">{d["title"]}</h4><p class="list-group-item-text" style="color:red;">{d["created"]} {d["stock_nickname"]} {d["stock_id"]}</p></a>'
            news_list.append(html_str)
        if loc == 'nfsf':
            html_str = f'<a href="{d["link"]}" class="list-group-item"><h4 class="list-group-item-heading">{d["title"]}</h4><p class="list-group-item-text" style="color:red;">{d["created"]} 國安基金</p></a>'
            news_list.append(html_str)
        if loc == 'cnsf':
            html_str = f'<a href="{d["link"]}" class="list-group-item"><h4 class="list-group-item-heading">{d["title"]}</h4><p class="list-group-item-text" style="color:red;">{d["created"]} 平準基金</p></a>'
            news_list.append(html_str)
    return {'code': 1, 'data': '\n'.join(news_list), 'msg': '獲取成功'}