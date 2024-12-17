# -*- coding: utf-8 -*-
# @Time : 2024/5/22  11:42
# @Author : Andy Hsieh
# @Desc :
import asyncio
import time

import pendulum
from decimal import Decimal
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from fastapi.requests import Request
from sse_starlette.sse import EventSourceResponse
from settings import msg_content
from utils.func import tsFormat, get_billable_weight_estimator, demo_requests
from utils.task import world_finance_task, income_task
from database import mongoClient, redisClient
from charts.common import usd2nt_Line
from requestBody import ShipBody, CompareBody

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


@common_router.post('/message')
async def create_message(content: str = Query(...)):
    try:
        msg_content.content = content
        print('api=', msg_content.content)
        return {'code': 1, 'data': None, 'msg': 'send success'}
    except:
        return {'code': 0, 'data': None, 'msg': 'send fail'}


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
async def latest_world_finance(
        request: Request,
        page: int = Query(default=1),
        size: int = Query(default=15),
        db=Depends(mongoClient)):
    keys = ['date','US10Y-Y', 'US10Y-Y△%', 'USIND', 'USIND△%', 'DJIA', 'DJIA△%', 'NASDAQ', 'NASDAQ△%', 'SOX',
                     'SOX△%', 'HSIND', 'HSIND△%', 'SSEC', 'SSEC△%', 'CSI300', 'CSI300△%',
                     'FI-NET', 'FI-Future-OI', 'FI-Option-OI', 'PC-R', 'US/NT', 'Top5Position',
                     'Top10Position', 'BullBearIND-R']
    keys += ['E-Mini NASDAQ FC', 'E-Mini NASDAQ UP%', 'E-Mini S&P FC', 'E-Mini S&P UP%', 'VIX FC', 'VIX UP%', 'E-Mini YM FC', 'E-Mini YM UP%', 'A50 FC', 'A50 UP%', 'HS FC', 'HS UP%']
    model = db.world_stock
    total = await model.count_documents({})
    total_page, left = divmod(total, size)
    total_page = total_page if not left else total_page + 1
    queryset = model.find({}, {'_id': 0}).sort([('date', -1)]).skip((page - 1) * size).limit(size)
    new_data = list()
    async for q in queryset:
        item = dict()
        q['date'] = tsFormat(q['date'])
        item.update(q)
        new_data.append(item)

    return templates.TemplateResponse(
        'demo_wf.html',
        {
            'request': request,
            'data': new_data,
            'cur_page': page,
            'total_page': total_page,
            'previous': False if page == 1 else True,
            'next': False if page == total_page else True,
            'keys': keys,
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


@common_router.get('/industry_fund')
async def industry_fund(request: Request, db=Depends(mongoClient)):
    industry_list = db.industrytable.find({}, {'_id': 0, 'type': 1})
    industries = [i['type'] async for i in industry_list]
    toolbars = [industries[idx: idx+9] for idx in range(0, len(industries), 9)]
    return templates.TemplateResponse(
        'fund2.html',
        {
            'request': request,
            'toolbars': toolbars
        },
    )


@common_router.get('/ship_estimator')
async def ship_estimator(request: Request):
    return templates.TemplateResponse(
        'ship.html',
        {
            'request': request,
        },
    )


@common_router.post('/ship/calculator')
async def ship_price_calculator(body: ShipBody, rdb=Depends(redisClient)):
    rows = body.row_data
    time.sleep(1)
    token = await rdb.get('bob:token')
    print(rows)
    print(token)
    ship_result = []
    for r in rows:
        temp_result = []
        for pt in [1, 2, 8]:
            res = get_billable_weight_estimator(token=token, length=r[0], width=r[1], height=r[2], weight=r[3], quantity=r[-1], pack=pt)
            temp_result.append(res)
            time.sleep(0.5)
        ship_result.append(temp_result)

    table_html = '<table class="table"><thead><tr><th>#</th><th>size</th><th>weight</th><th>quantity</th><th>BillableBox</th><th>BillableBubbleMailer</th><th>BiilableShipInOwn</th></tr></thead><tbody>{content}</tbody></table>'
    body_str = ''
    for r in range(len(rows)):
        body_str += f'<tr><th scope="row"><input type="checkbox" class="row-checkbox"></th><td>{rows[r][0]}x{rows[r][1]}x{rows[r][2]}</td><td>{rows[r][3]}</td><td>{rows[r][4]}</td><td>{ship_result[r][0]}</td><td>{ship_result[r][1]}</td><td>{ship_result[r][2]}</td></tr>'

    table_str = table_html.format(content=body_str)
    return table_str



@common_router.post('/ship/comparator')
async def ship_price_calculator(body: CompareBody,
                                rdb=Depends(redisClient)
                                ):
    rows = body.row_data
    print('rows=', rows)
    ship_weight_array = [[int(Decimal(r[3].split(',')[0].replace('oz', ''))), int(Decimal(r[4].split(',')[0].replace('oz', ''))), int(Decimal(r[5].split(',')[0].replace('oz', '')))] for r in rows]
    print('swa= ', ship_weight_array)
    zone_price_list = []
    async with rdb.pipeline(transaction=True) as pipe:
        zone_weight = await pipe.lrange("bob:zone_weight", 0, -1).execute()
        if zone_weight:
            zone_weight = zone_weight[0]
        else:
            raise ValueError('miss zw')
        for weight_list in ship_weight_array:
            for w in weight_list:
                pipe.lrange(f"bob:oz:{w}", 0, -1)
            row_weight = await pipe.execute()
            zone_price_list.append(row_weight)
    print('zw = ', zone_weight)
    print('ZPL', zone_price_list)
    result_rows = []
    box_init, bubble_init, own_init = 0, 0, 0
    for r in range(len(rows)):
        temp_rows = rows[r][:3]
        box_price = round(sum([Decimal(zone_weight[i]) * Decimal(zone_price_list[r][0][i]) for i in range(len(zone_weight))])/Decimal('100'), 2) if zone_price_list[r][0] else 0
        bubble_price = round(sum([Decimal(zone_weight[i]) * Decimal(zone_price_list[r][1][i]) for i in range(len(zone_weight))])/Decimal('100'), 2) if zone_price_list[r][1] else 0
        own_price = round(sum([Decimal(zone_weight[i]) * Decimal(zone_price_list[r][2][i]) for i in range(len(zone_weight))])/Decimal('100'), 2) if zone_price_list[r][2] else 0
        if r == 0:
            box_init, bubble_init, own_init = box_price, bubble_price, own_price
            temp_rows += [box_price, bubble_price, own_price, 0, 0, 0]
        else:
            temp_rows += [box_price, bubble_price, own_price, box_price - box_init, bubble_price - bubble_init, own_price - own_init]
        result_rows.append(temp_rows)
    print('result rows = ', result_rows)
    table_html = ''
    table_html = '<table class="table"><thead><tr><th>size</th><th>weight</th><th>quantity</th><th>BillableBoxPrice</th><th>BillableBubbleMailerPrice</th><th>BiilableShipInOwnPrice</th><th>BoxPriceDiffer</th><th>BubbleMailerPriceDiffer</th><th>ShipInOwnPricePriceDiffer</th></tr></thead><tbody>{content}</tbody></table>'
    body_str = ''
    for r in result_rows:
        body_str += f'<td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td><td>{r[6]}</td><td>{r[7]}</td><td>{r[8]}</td></tr>'
    table_str = table_html.format(content=body_str)
    return table_str


@common_router.get('/rdb/test')
async def spider_test(rdb=Depends(redisClient)):
    weight_list = [2, 3, 4]
    async with rdb.pipeline(transaction=True) as pipe:
        for w in weight_list:
            pipe.lrange(f"oz:{w}", 0, -1)
        res = await pipe.execute()
        print(res)
    return 'ok'