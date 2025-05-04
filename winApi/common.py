# -*- coding: utf-8 -*-
# @Time : 2024/5/22  11:42
# @Author : Andy Hsieh
# @Desc :
import asyncio
import time,json
from typing import List, Optional

import pendulum
from decimal import Decimal
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from fastapi.requests import Request
from sse_starlette.sse import EventSourceResponse
from starlette.responses import StreamingResponse

from settings import msg_content
from utils.func import tsFormat, list_to_nested_dict
from utils.task import world_finance_task, income_task
from database import mongoClient, redisClient
from charts.common import usd2nt_Line
from requestBody import ShipBody, CompareBody, DimensionRequest
notifications = asyncio.Queue()
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


@common_router.post("/send_notification/")
async def send_notification(notification: dict):
    """模拟服务器接收新通知并广播"""
    print('received message', notification)
    await notifications.put(json.dumps(notification))
    return {"status": "success"}


@common_router.get("/stream_notifications/")
async def stream_notifications():
    """提供SSE流服务"""

    async def event_generator():
        while True:
            notification = await notifications.get()
            print('send message', notification)
            yield f"data: {notification}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")



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


@common_router.post("/dimensions", response_model=List)
def calculate_dimensions(request_data: DimensionRequest):
    unique_dimensions = set()
    min_length = request_data.min_length
    max_length = request_data.max_length
    min_width = request_data.min_width
    max_width = request_data.max_width
    min_height = request_data.min_height
    max_height = request_data.max_height
    weight = request_data.weight
    q_min = request_data.q_min
    q_max = request_data.q_max
    for length in range(min_length, max_length+1):  # 长度范围
        for width in range(min_width, max_width+1):  # 宽度范围
            for height in range(min_height, max_height+1):  # 高度范围
                dimension = tuple(sorted([length, width, height], reverse=True))
                unique_dimensions.add(dimension)
    dimensions = sorted([list(tup) for tup in unique_dimensions], reverse=True)

    result = []
    for q in range(q_min, q_max+1):
        for d in dimensions:
            r = d.copy()
            r += [q, weight]
            result.append(r)
    return result


@common_router.post('/ship/calculator')
async def ship_price_calculator(body: ShipBody, rdb=Depends(redisClient)):
    rows = body.row_data
    for r in rows:
        await rdb.rpush(f"task:{int(time.time())}", str(r))
    return 'ok'



@common_router.get("/detail")
async def estimator_detail(request: Request, key: Optional[str] = Query(default=''), rdb=Depends(redisClient)):

    task_names = await rdb.keys('result*')
    task_names = [name for name in task_names]
    task_names.sort()
    if not key:
        task_queue = await rdb.lrange(task_names[0], 0, -1)
    else:
        task_names.remove(key)
        task_names = [key] + task_names
        task_queue = await rdb.lrange(key, 0, -1)

    tasks = [eval(d) for d in task_queue]
    result_data, quantity_list, og_size_list = list_to_nested_dict(data=tasks)
    quantity_list.sort()
    og_size_list.sort()

    html_list = []
    for q in quantity_list:
        tbody_str = ''
        for s in og_size_list:
            size_part = f'<td><label><input type="radio" name="og-size-{q}" value="{s},{q}"> {s}</label></td>'
            box = f"<td>{result_data[q][s]['Box']['Box']['size']} / {result_data[q][s]['Box']['Box']['weight']}(oz) / ${result_data[q][s]['Box']['Box']['price']}</td>"
            bb = f"<td>{result_data[q][s]['Bubble Mailer']['Bubble Mailer']['size']} / {result_data[q][s]['Bubble Mailer']['Bubble Mailer']['weight']}(oz) / ${result_data[q][s]['Bubble Mailer']['Bubble Mailer']['price']}</td>"
            sio = f"<td>{result_data[q][s]['Ship in Own']['Ship in Own']['size']} / {result_data[q][s]['Ship in Own']['Ship in Own']['weight']}(oz) / ${result_data[q][s]['Ship in Own']['Ship in Own']['price']}</td>"
            tbody_str += f'<tr>{size_part}{box}{bb}{sio}</tr>'
        html_list.append(f'<div class="panel panel-default" style="margin-top: 8px"><div class="panel-heading"><h4>數量 {q} 區塊</h4></div><div class="panel-body"><table id="taskTable{ q }" class="table table-striped table-bordered"><thead><tr><th>OG-SIZE</th><th>Box</th><th>Bubble Mailer</th><th>Ship in Own</th></tr></thead><tbody>{tbody_str}</tbody></table></div></div>')
    html_str = '\n'.join(html_list)
    return templates.TemplateResponse("ship_detail.html",
                                      {
                                          "request": request,
                                          "task_names": task_names,
                                          "html_str": html_str,
                                      })



@common_router.post('/comparator')
async def ship_price_comparator(body: CompareBody,
                                rdb=Depends(redisClient)
                                ):
    print(body.row_data, body.task_name)
    standard = body.row_data
    task_queue = await rdb.lrange(body.task_name, 0, -1)
    tasks = [eval(d) for d in task_queue]
    result, quantity_list, og_size_list = list_to_nested_dict(data=tasks)
    quantity_list.sort()
    og_size_list.sort()
    big_map = dict()
    for obj in standard:
        size, nums = obj[0], int(obj[1])
        standard_box_info = result[nums][size]['Box']['Box']
        standard_bm_info = result[nums][size]['Bubble Mailer']['Bubble Mailer']
        standard_sio_info = result[nums][size]['Ship in Own']['Ship in Own']
        standard_az_info = result[1][size]['Amazon']['Amazon']
        big_map[nums] = []
        temp_size_list = og_size_list.copy()
        temp_size_list.remove(size)
        big_map[nums].append({
            'og_size': size,
            'AmazonInfo': f"{standard_az_info['size']} / {standard_az_info['weight']} / ${standard_az_info['price']}",
            'BoxInfo': f"{standard_box_info['size']} / {standard_box_info['weight']} / ${standard_box_info['price']}",
            'BMInfo': f"{standard_bm_info['size']} / {standard_bm_info['weight']} / ${standard_bm_info['price']}",
            'SIOInfo': f"{standard_sio_info['size']} / {standard_sio_info['weight']} / ${standard_sio_info['price']}",
            'Box Differ': Decimal('0'),
            'Bubble Mailer Differ': Decimal('0'),
            'Ship in Own Differ': Decimal('0')})
        for ts in temp_size_list:
            item = {
                'og_size': ts,
                'AmazonInfo': f"{result[1][ts]['Amazon']['Amazon']['size']} / {result[1][ts]['Amazon']['Amazon']['weight']} / ${result[1][ts]['Amazon']['Amazon']['price']}",
                'BoxInfo': f"{result[nums][ts]['Box']['Box']['size']} / {result[nums][ts]['Box']['Box']['weight']} / ${result[nums][ts]['Box']['Box']['price']}",
                'BMInfo': f"{result[nums][ts]['Bubble Mailer']['Bubble Mailer']['size']} / {result[nums][ts]['Bubble Mailer']['Bubble Mailer']['weight']} / ${result[nums][ts]['Bubble Mailer']['Bubble Mailer']['price']}",
                'SIOInfo': f"{result[nums][ts]['Ship in Own']['Ship in Own']['size']} / {result[nums][ts]['Ship in Own']['Ship in Own']['weight']} / ${result[nums][ts]['Ship in Own']['Ship in Own']['price']}",
                'Box Differ': result[nums][ts]['Box']['Box']['price'] - standard_box_info['price'],
                'Bubble Mailer Differ': result[nums][ts]['Bubble Mailer']['Bubble Mailer']['price'] - standard_bm_info[
                    'price'],
                'Ship in Own Differ': result[nums][ts]['Ship in Own']['Ship in Own']['price'] - standard_sio_info['price']
            }
            big_map[nums].append(item)

    html_list = []
    for q in quantity_list:
        tbody_str = ''
        for obj in big_map[q]:
            print(obj)
            size_part = f'<td>{obj["og_size"]}</td>'
            am = f"<td>{obj['AmazonInfo']}</td>"
            box = f"<td>{obj['BoxInfo']}</td>"
            bb = f"<td>{obj['BMInfo']}</td>"
            sio = f"<td>{obj['SIOInfo']}</td>"
            bd = f"<td>{obj['Box Differ']}</td>"
            bmd = f"<td>{obj['Bubble Mailer Differ']}</td>"
            sd = f"<td>{obj['Ship in Own Differ']}</td>"
            tbody_str += f'<tr>{size_part}{am}{box}{bb}{sio}{bd}{bmd}{sd}</tr>'
        html_list.append(f'<div class="panel panel-default" style="margin-top: 8px"><div class="panel-heading"><h4>數量 {q} 區塊</h4></div><div class="panel-body"><table id="taskTable{ q }" class="table table-striped table-bordered"><thead><tr><th>OG-SIZE</th><th>AmazonInfo</th><th>BoxInfo</th><th>BMInfo</th><th>SIOInfo</th><th>Box Differ</th><th>Bubble Mailer Differ</th><th>Ship in Own Differ</th></tr></thead><tbody>{tbody_str}</tbody></table></div></div>')
    html_str = '\n'.join(html_list)
    return html_str


@common_router.get('/rdb/test')
async def spider_test(rdb=Depends(redisClient)):
    weight_list = [2, 3, 4]
    async with rdb.pipeline(transaction=True) as pipe:
        for w in weight_list:
            pipe.lrange(f"oz:{w}", 0, -1)
        res = await pipe.execute()
        print(res)
    return 'ok'