# -*- coding: utf-8 -*-
# @Time : 2023/12/28  下午 12:26
# @Author : Andy Hsieh
# @Desc :
import hashlib
import pendulum
import uvicorn, os, datetime
from fastapi import FastAPI, Request, Depends
from fastapi import Path, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import mongo_connector, redis_cache
from utils import tsFormat, stockChart, BadException, ForbiddenException, markLine, message_generator
from serialize import CompanyModel, GroupBody, GroupListBody, NewsTaskBody, NoteBody
from settings import msg_content
from sse_starlette.sse import EventSourceResponse


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory='templates')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.exception_handler(BadException)
def bad_exception_handler(request: Request, exc: BadException):
    return JSONResponse(
        status_code=400,
        content={'code': -1, 'data': None, 'msg': f'{exc.msg}'},
    )


@app.exception_handler(ForbiddenException)
def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=403,
        content={'code': -1, 'data': None, 'msg': f'{exc.msg}'},
    )


@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse(
        'home.html',
        {
            'request': request,
        },
    )


@app.post('/message')
async def create_message(content: str = Query(...)):
    try:
        msg_content.content = content
        print('api=', msg_content.content)
        return {'code': 1, 'data': None, 'msg': 'send success'}
    except:
        return {'code': 0, 'data': None, 'msg': 'send fail'}


@app.get("/notification")
async def root(request: Request):
    event_generator = message_generator(request)
    return EventSourceResponse(event_generator)


@app.get('/news_24hr')
async def news_in_time(db=Depends(mongo_connector)):


    # temp_content = CONTENT
    # async for n in news_set:
    #     n['created'] = pendulum.from_timestamp(pendulum.parse(str(n['created']),tz='UTC').timestamp(), tz='Asia/Taipei').format('YYYY-MM-DD HH:mm:ss')
    #     news_res.append(temp_content.format(stock_id=n['stock_id'],created=n['created'],link=n['link'],title=n['title']))
    # body_html = '\n'.join(news_res)
    # table_html = TABLE.format(body=body_html)

    return {'code':1, 'data':'stocks', 'msg': '成功'}


@app.get('/groups/index')
async def groups_page(request: Request,
                      db=Depends(mongo_connector)):
    group_base = db.groups.find({}, {'_id': 0}).sort([('_id', 1)])
    group_basedata = [t async for t in group_base]

    group = {
        '$group': {
            '_id': "$group_id",
            "stocks": {"$push": "$stock_id"}
        }
    }
    stock_teams = db.group_news.aggregate([group])

    everygroup = dict()
    distincList = list()
    async for t in stock_teams:
        everygroup[t['_id']] = t['stocks']
        distincList += t['stocks']

    unique_stocks = list(set(distincList))

    news_set = db.news.find({"$and": [{'created': {'$gte': pendulum.now(tz='Asia/Taipei').add(hours=-24)}},
                                      {'stock_id': {'$in': unique_stocks}}]}, {'_id': 0}).sort([('_id', -1)])
    news_map = dict()
    async for n in news_set:
        n['created'] = pendulum.from_timestamp(pendulum.parse(str(n['created']), tz='UTC').timestamp(),
                                               tz='Asia/Taipei').format('YYYY-MM-DD HH:mm:ss')

        if n['stock_id'] not in news_map:
            news_map[n['stock_id']] = [n]
        else:
            news_map[n['stock_id']] += [n]

    for g in group_basedata:
        g['news_detail'] = list()
        list_set = everygroup.get(g['uid'])
        if not list_set:
            continue
        for s in list_set:
            g['news_detail'] += news_map.get(s, [])

    nfsf_gen = db.nfsf.find({'created': {'$gte': pendulum.now(tz='Asia/Taipei').add(hours=-24)}}, {'_id': 0}).sort([('_id', -1)])
    nfsf_set = [n async for n in nfsf_gen]

    cnsf_gen = db.cnsf.find({'created': {'$gte': pendulum.now(tz='Asia/Taipei').add(hours=-24)}}, {'_id': 0}).sort(
        [('_id', -1)])
    cnsf_set = [n async for n in cnsf_gen]

    return templates.TemplateResponse(
        'tab.html',
        {
            'request': request,
            'groups': group_basedata,
            'nfsf_set': nfsf_set,
            'cnsf_set': cnsf_set
        },
    )


@app.post('/addGroupList')
async def add_groupList(body: GroupListBody,
                        db=Depends(mongo_connector)):
    name_list = list()
    try:
        for g in body.groups:
            item = {
                'stock_id': body.stock_id,
                'stock_nickname': body.stock_nickname,
                'group_id': g['uid']
            }
            await db.group_news.update_one({'group_id': g['uid'], 'stock_id': body.stock_id},
                                           {'$set': item},
                                           upsert=True)

            name_list.append(g['title'])

            msg = f'股票代號 {body.stock_id} 已加入清單{"、".join(name_list)}'
            return {'code': 1, 'data': None, 'msg': msg}
    except Exception as e:
        print('add groupList error', e)
        return {'code': 0, 'data': None, 'msg': '系統錯誤'}


@app.post('/addGroup')
async def create_group(body: GroupBody,
                       db=Depends(mongo_connector)):
    try:
        model = db.groups
        print('title', body.title)
        uuid = hashlib.md5(body.title.encode()).hexdigest()
        item = {
            'title': body.title,
            'uid': uuid
        }
        print(item)
        target = await model.find_one({'uid': uuid})
        if not target:
            await model.insert_one(item)
        print('---', item)
        return {'code':1, 'data': {'title': body.title, 'uid':uuid}, 'msg': '建立成功'}
    except Exception as e:
        print(e)
        return {'code': 0, 'data': '123', 'msg': 'create fail'}


@app.get('/groups/list')
async def get_groups(db=Depends(mongo_connector)):
    try:
        groups = db.groups.find({},{'_id': 0})
        htmlList = list()
        async for g in groups:
            html = f'''
            <div style = "margin-bottom: 5px;text-align: center">
                <button task_id = "{g['uid']}" type = "button" class ="btn-lg btn-primary" style="width: 80%" onclick="startTaskEvent(this)">{g['title']}</button>
            </div>
            '''
            htmlList.append(html)
        content = '\n'.join(htmlList)
        return {'code': 1, 'data': content, 'msg': 'success'}
    except:
        return {'code': 0, 'data': None, 'msg': '未知錯誤'}


@app.post('/addTask')
async def add_newsTask(body: NewsTaskBody,
                       rdb = Depends(redis_cache)):
    try:
        print(body.uid)
        await rdb.rpush('news_task', body.uid)
        return {'code': 1, 'data': None, 'msg': '任務已啟動'}
    except:
        return {'code': 0, 'data': None, 'msg': '任務啟動失敗'}


@app.get('/statistic/recruitment')
async def recruiment_trend(db=Depends(mongo_connector)):
    match = {
        '$match': {
            'needMinEmp': {
                '$ne': 0
            },
            'stock_id': {
                '$nin': ['0050', '0056', '00878']
            }
        }
    }

    group = {
        '$group': {
            '_id': "$date",
            'count': {'$sum': 1}
        }
    }

    sort_dict = {
        '$sort': {
            '_id': 1
        }
    }

    res = db.companydata.aggregate([match, group, sort_dict])
    x_data, y_data = list(), list()
    async for r in res:
        x_data.append(pendulum.parse(str(r['_id'])).add(hours=8).format('YYYY/MM/DD'))
        y_data.append(r['count'])
    chart = markLine('招聘趨勢',x_data, y_data)
    return chart.dump_options_with_quotes()


@app.get('/trend/recruitment')
async def recruitment_chart(request: Request):
    return templates.TemplateResponse(
        'trend.html',
        {
            'request': request,
        },
    )


@app.get('/statistic/news')
async def statistic_news(stock_id: str = Query(..., pattern='\d+'),
                         company: str = Query(...),
                         db=Depends(mongo_connector)):
    data = db.newsCount.find({'stock_id': stock_id, }, {'date': 1, 'count': 1}).sort([('date', 1)])
    x_data, y_data = list(), list()
    async for d in data:
        try:
            x_data.append(pendulum.parse(str(d['date'])).add(hours=8).format('YYYY/MM/DD'))
            y_data.append(d.get('count',0))
        except:
            continue
    chart = markLine(f'{company}-新聞趨勢',x_data, y_data)
    return chart.dump_options_with_quotes()


@app.get('/trend/news/{stock_id}')
async def trends_news(request:Request,
                      stock_id: str = Path(..., pattern='\d+'),
                      db=Depends(mongo_connector)):
    stock = await db.company2.find_one({'stock_id': stock_id}, {'stock_id': 1,'nickname': 1})
    if not stock:
        return templates.TemplateResponse(
            'news.html',
            {
                'request': request,
                'stock_id': stock_id,
                'stock_nickname': stock['nickname'],
                'news_set': [],
                'group': []
            },
        )

    news_set = db.news.find({'stock_id': stock_id,
                           'created': pendulum.today(tz='Asia/Taipei')},
                          {'_id':0})
    news_set = [n async for n in news_set]

    group_gen = db.groups.find({}, {'_id': 0})
    group_list = [group async for group in group_gen]

    return templates.TemplateResponse(
        'news.html',
        {
            'request': request,
            'stock_id': stock_id,
            'news_set': news_set,
            'group': group_list,
            'stock_nickname': stock['nickname'],
        },
    )


@app.get('/img/{stock_id}')
async def get_img(
        stock_id: str = Path(..., pattern='\d+'),
        db=Depends(mongo_connector)
):
    stock = await db.company2.find_one({'stock_id': stock_id},{'employees':1})
    if not stock:
        return {}
    emps = stock.get('employees',0)
    stock_data = db.companydata.find({'stock_id': stock_id},
                                     {'jer_max': 1, 'jer_min': 1,'jer_full_min':1, 'jer_full_max' :1, 'date': 1, 'differenceSetCount': 1,
                                      'jobOffCount': 1,}).sort([('date', 1)])
    jer_min = []
    jer_max = []
    jer_f_min = []
    jer_f_max = []
    date_arr = []
    differ_set = []
    job_offs = []
    async for s in stock_data:
        date_arr.append(str((s['date'] + datetime.timedelta(hours=8))))
        jer_max.append(s['jer_max'])
        jer_min.append(s['jer_min'])
        jer_f_max.append(s.get('jer_full_max',0))
        jer_f_min.append(s.get('jer_full_min', 0))
        differ_set.append(s['differenceSetCount'])
        job_offs.append(s['jobOffCount'])
    print(date_arr)
    print(jer_min)
    bar = stockChart(date_arr, jer_min, jer_max, jer_f_min, jer_f_max, differ_set, job_offs, emps)
    return bar.dump_options_with_quotes()


@app.get('/chart/{stock_id}')
async def getStockChart(
        request: Request,
        stock_id: str = Path(..., pattern='\d+'),

):
    return templates.TemplateResponse(
        'chart.html',
        {
            'request': request,
            'stock_id': stock_id,
        },
    )



@app.get('/stock/world')
async def get_world(request: Request,
                    page: int = Query(default=1),
                    size: int = Query(default=30),
                    db=Depends(mongo_connector)):
    filter = dict()
    model = db.world_stock
    total = await model.count_documents(filter)
    total_page, left = divmod(total, size)
    total_page = total_page if not left else total_page + 1
    queryset = model.find(filter, {'_id': 0}).sort([('date', -1)]).skip((page - 1) * size).limit(size)
    dataset = [q async for q in queryset]

    return templates.TemplateResponse(
        'world_list.html',
        {
            'request': request,
            'data': dataset,
            'keys': ['date', 'US10Y-Y', 'US10Y-Y△%', 'USIND', 'USIND△%', 'DJIA', 'DJIA△%', 'NASDAQ', 'NASDAQ△%', 'SOX',
                     'SOX△%', 'FI-NET', 'FI-Future-OI', 'FI-Option-OI', 'PC-R', 'US/NT', 'Top5Position',
                     'Top10Position', 'BullBearIND-R'],
            'previous': False if page == 1 else True,
            'next': False if page == total_page else True,
            'cur_page': page,
            'total_page': total_page,
            'formatter': tsFormat
        },
    )


@app.get('/company/list')
async def get_company(request: Request,
                      stock_id: str = Query(default=''),
                      page: int = Query(default=1),
                      size: int = Query(default=100),
                      db=Depends(mongo_connector)):

    filter = {'stock_id': {'$in':stock_id.split(',')}} if stock_id else dict()
    model = db.company2
    total = await model.count_documents(filter)
    print(total)
    total_page, left = divmod(total, size)
    total_page = total_page if not left else total_page + 1
    queryset = model.find(filter, {'_id':0,'nickname': 1, 'stock_id': 1, 'employees': 1}).sort('_id', -1).skip((page - 1) * size).limit(size)
    dataset = [q async for q in queryset]
    return templates.TemplateResponse(
        'company.html',
        {
            'request': request,
            'data': dataset,
            'cur_page': page,
            'total_page': total_page,
            'previous': False if page == 1 else True,
            'next': False if page == total_page else True,
            'sid': stock_id
        },
    )


@app.get('/api/eps/{stock_id}')
async def retrieve_company_eps(stock_id: str = Path(...),
                           db=Depends(mongo_connector)):
    try:
        model = db.company2
        res = await model.find_one({'stock_id': stock_id},
                                   {'_id':0, 'nickname': 1, 'stock_id': 1, 'employees': 1,
                                    'closePrice': 1, 'pbr': 1, 'per_w_1': 1, 'per_w_2': 1, 'per_w_3': 1,
                                    'per_w1': 1, 'per_w2': 1, 'per_w3': 1, })
        print(res)
        if not res:
            return {'code': 0}
        return {'code': 1, 'data': res}
    except Exception as e:
        print(e)
        raise ForbiddenException(msg='server error')


@app.get('/api/company/{stock_id}')
async def retrieve_company(stock_id: str = Path(...),
                           db=Depends(mongo_connector)):
    try:
        model = db.company2
        res = await model.find_one({'stock_id': stock_id},
                                   {'_id':0, 'nickname': 1, 'stock_id': 1, 'employees': 1,
                                    'closePrice': 1, 'pbr': 1, 'per_w_1': 1, 'per_w_2': 1, 'per_w_3': 1,
                                    'per_w1': 1, 'per_w2': 1, 'per_w3': 1, })
        print(res)
        if not res:
            return {'code': 0}
        return {'code': 1, 'data': res}
    except Exception as e:
        print(e)
        raise ForbiddenException(msg='server error')


@app.put('/api/company/{stock_id}')
async def update_company(body: CompanyModel,
                         stock_id: str = Path(...),
                         db=Depends(mongo_connector)):
    try:
        print(body)
        if body.plot:
            if body.plot.startswith('('):
                body.plot = body.plot.replace(body.plot[1:4], pendulum.today(tz="Asia/Taipei").format("MMM"))
            else:
                body.plot = f'({pendulum.today(tz="Asia/Taipei").format("MMM")}){body.plot}'
        if body.state:
            if body.state.startswith('('):
                body.state = body.state.replace(body.state[1:4], pendulum.today(tz="Asia/Taipei").format("MMM"))
            else:
                body.state = f'({pendulum.today(tz="Asia/Taipei").format("MMM")}){body.state}'
        model = db.company2
        target = await model.update_one({'stock_id': stock_id},
                                        {'$set': body.__dict__})

        if not target.modified_count:
            return {'code': 0}
        return {'code': 1}

    except Exception as e:
        print(e)
        raise ForbiddenException(msg='server error')


@app.delete('/api/company/{stock_id}')
async def delete_company(stock_id: str = Path(...),
                         db=Depends(mongo_connector)):
    # try:
    #     model = db.company
    #     res = await model.delete_many({'stock_id': stock_id})
    #     if not res.deleted_count:
    #         return {'code': 0}
    #     return {'code': 1}
    # except Exception as e:
    #     print(e)
    #     raise ForbiddenException(msg='server error')
    raise ForbiddenException(msg='功能尚未開放')


@app.post('/api/note')
async def create_note(body: NoteBody,
                      db=Depends(mongo_connector)):
    try:
        target = await db.company2.find_one({'stock_id': body.stock_id})
        if not target:
            return {'code': 0, 'data': None, 'msg': 'Stock is not exist!'}
        note_item = {
            'stock_id': body.stock_id,
            'note': body.note,
            'created': pendulum.now(tz='Asia/Taipei').format('YYYY-MM-DD HH:mm:ss')
        }
        await db.note.insert_one(note_item)
        return {'code': 1, 'data': None, 'msg': 'Note success!'}
    except:
        return {'code': 0, 'data': None, 'msg': 'Note fail!'}


@app.get('/api/note')
async def retrive_note(stock_id: str=Query(...),
                      db=Depends(mongo_connector)):
    try:
        target = await db.company2.find_one({'stock_id': stock_id})
        if not target:
            return {'code': 0, 'data': None, 'msg': 'Stock is not exist!'}
        data = db.note.find({'stock_id': stock_id}).sort([('_id', -1)]).limit(5)
        html_list = list()
        async for d in data:
            html_str = f'''
            <tr>
                <th scope="row">{d["note"]}</th>
                <td>{d["created"]}</td>
            </tr>'''
            html_list.append(html_str)
        html_content = '\n'.join(html_list)
        return {'code': 1, 'data': html_content, 'msg': 'Note success!'}
    except:
        return {'code': 0, 'data': '', 'msg': 'Note fail!'}


if __name__ == '__main__':
    uvicorn.run('manage:app', host='0.0.0.0', port=5000, reload=True)
