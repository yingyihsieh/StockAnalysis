# -*- coding: utf-8 -*-
# @Time : 2024/5/20  17:50
# @Author : Andy Hsieh
# @Desc :
import hashlib
import time
import pendulum
import datetime
from decimal import Decimal
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Depends, Query, Path
from fastapi.requests import Request
from requestBody import NewsTaskBody, NoteBody, EPSBody, GroupBody, GroupItemBody
from database import mongoClient, redisClient
from utils.func import tsFormat
from charts.tw import HolderLine, TopHolderLine, stockChart

tw_router = APIRouter()
templates = Jinja2Templates(directory='templates')


@tw_router.get('/company/list')
async def get_tw_company(request: Request,
                         stock_id: str = Query(default=''),
                         page: int = Query(default=1),
                         size: int = Query(default=100),
                         db=Depends(mongoClient)):
    filter = {'stock_id': {'$in': stock_id.split(',')}} if stock_id else dict()
    model = db.company2
    total = await model.count_documents(filter)
    print(total)
    total_page, left = divmod(total, size)
    total_page = total_page if not left else total_page + 1
    queryset = model.find(filter, {'_id': 0, 'nickname': 1, 'stock_id': 1, 'yoy-1': 1, 'mom-1': 1, 'updated': 1}).sort('_id', -1).skip(
        (page - 1) * size).limit(size)
    dataset = [q async for q in queryset]
    return templates.TemplateResponse(
        'twCompany.html',
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


@tw_router.get('/income/latest')
async def tw_income(request: Request,
                    stock_id: str = Query(default=''),
                    page: int = Query(default=1),
                    size: int = Query(default=100),
                    db=Depends(mongoClient)):
    filter = {'stock_id': {'$in': stock_id.split(',')}} if stock_id else dict()
    model = db.company2
    total = await model.count_documents(filter)
    total_page, left = divmod(total, size)
    total_page = total_page if not left else total_page + 1
    queryset = model.find(filter, {'_id': 0, 'nickname': 1, 'stock_id': 1, 'yoy-1': 1, 'mom-1': 1, 'updated': 1}).sort(
        [('updated', -1), ('yoy-1', -1)]).skip(
        (page - 1) * size).limit(size)

    dataset = [{
        'nickname': q['nickname'],
        'stock_id': q['stock_id'],
        'yoy': q['yoy-1'],
        'mom': q['mom-1'],
        'updated': q.get('updated'),
    } async for q in queryset if q['stock_id'] not in ['0050', '0056', '00878']]

    return templates.TemplateResponse(
        'income.html',
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


@tw_router.get('/groups/choice_list')
async def get_tw_gp_choice_list(db=Depends(mongoClient)):
    try:
        groups = db.groups.find({}, {'_id': 0})
        htmlList = list()
        async for g in groups:
            html = f'<option value="{g["uid"]}">{g["title"]}</option>'
            htmlList.append(html)
        content = '\n'.join(htmlList)
        return {'code': 1, 'data': content, 'msg': 'success'}
    except:
        return {'code': 0, 'data': None, 'msg': '未知錯誤'}


@tw_router.get('/groups/list')
async def get_tw_groups(task:bool = Query(default=False),
                        db=Depends(mongoClient)):
    try:
        groups = db.groups.find({}, {'_id': 0})
        htmlList = list()
        async for g in groups:
            if task:
                html = f'''
                <div style = "margin-bottom: 5px;text-align: center">
                    <button task_id = "{g['uid']}" type = "button" class ="btn-lg btn-primary" style="width: 80%" onclick="startTwEvent(this)">{g['title']}</button>
                </div>
                '''
            else:
                html = f'<li class="list-group-item" id="{g["uid"]}">{g["title"]}</li>'
            htmlList.append(html)
        content = '\n'.join(htmlList)
        return {'code': 1, 'data': content, 'msg': 'success'}
    except:
        return {'code': 0, 'data': None, 'msg': '未知錯誤'}


@tw_router.post('/groups')
async def create_tw_group(body: GroupBody,
                          db=Depends(mongoClient)):
    try:
        model = db.groups
        print('title', body.title)
        uuid = hashlib.md5(body.title.encode()).hexdigest()
        item = {
            'title': body.title,
            'uid': uuid
        }

        target = await model.find_one({'uid': uuid})
        if not target:
            await model.insert_one(item)

        return {'code': 1, 'data': {'title': body.title, 'uid': uuid}, 'msg': '建立成功'}
    except Exception as e:
        print(e)
        return {'code': 0, 'data': '123', 'msg': 'create fail'}


@tw_router.post('/groupItem')
async def add_groupList(body: GroupItemBody,
                        db=Depends(mongoClient)):
    try:
        item = {
            'stock_id': body.stock_id,
            'stock_nickname': body.stock_nickname,
            'group_id': body.group_id
        }

        await db.group_news.update_one({'group_id': item['group_id'], 'stock_id': body.stock_id},
                                       {'$set': item},
                                       upsert=True)


        msg = f'{body.stock_nickname} 股票代號 {body.stock_id} 加入 {body.group_name} 成功!'
        return {'code': 1, 'data': None, 'msg': msg}
    except Exception as e:
        print('add groupList error', e)
        return {'code': 0, 'data': None, 'msg': '系統錯誤'}


@tw_router.delete('/groupItem')
async def add_groupList(stock_id: str=Query(...),
                        group_id: str=Query(...),
                        db=Depends(mongoClient)):
    try:

        await db.group_news.delete_one({'group_id': group_id, 'stock_id': stock_id})

        return {'code': 1, 'data': None, 'msg': 'delete success'}
    except Exception as e:
        print('add groupList error', e)
        return {'code': 0, 'data': None, 'msg': 'something wrong'}


@tw_router.post('/addTask')
async def add_twNewsTask(body: NewsTaskBody,
                         rdb=Depends(redisClient)):
    try:
        item = {'uid': body.uid, 'loc': 'tw'}
        await rdb.rpush('news_task', str(item))
        return {'code': 1, 'data': None, 'msg': '任務已啟動'}
    except:
        return {'code': 0, 'data': None, 'msg': '任務啟動失敗'}


@tw_router.get('/note')
async def retrieve_tw_note(stock_id: str = Query(...),
                          db=Depends(mongoClient)):
    try:
        data = db.note.find({'stock_id': stock_id}).sort([('_id', -1)]).limit(5)
        html_list = list()
        async for d in data:
            html_str = f'''<li class="list-group-item">{d["note"]}<span class="badge">{d["created"]}</span></li>'''
            html_list.append(html_str)
        html_content = '\n'.join(html_list)
        return {'code': 1, 'data': html_content, 'msg': 'Note success!'}
    except:
        return {'code': 0, 'data': '', 'msg': 'Note fail!'}


@tw_router.post('/note')
async def create_tw_note(body: NoteBody,
                      db=Depends(mongoClient)):
    try:
        note_item = {
            'stock_id': body.stock_id,
            'note': body.note,
            'created': pendulum.now(tz='Asia/Taipei').format('YYYY-MM-DD HH:mm:ss')
        }
        await db.note.insert_one(note_item)
        return {'code': 1, 'data': None, 'msg': 'Note success!'}
    except:
        return {'code': 0, 'data': None, 'msg': 'Note fail!'}


@tw_router.get('/eps/{stock_id}')
async def retrieve_company_eps(stock_id: str = Path(...),
                               db=Depends(mongoClient)):
    try:
        model = db.company2
        res = await model.find_one({'stock_id': stock_id},
                                   {'_id': 0, 'nickname': 1, 'stock_id': 1, 'employees': 1,
                                    'closePrice': 1, 'pbr': 1, 'per_w_1': 1, 'per_w_2': 1, 'per_w_3': 1,
                                    'per_w1': 1, 'per_w2': 1, 'per_w3': 1, })
        print(res)
        calculate_data = await db.eps.find({'stock_id': stock_id},
                                           {'_id': 0, 'eps': 1, 'per_1': 1,
                                            'per_2': 1, 'per_3': 1, 'per1': 1,
                                            'per2': 1, 'per3': 1}).sort([('_id', -1)]).limit(1).to_list(1)

        c_data = {} if not calculate_data else calculate_data[0]

        if not res:
            return {'code': 0, 'msg': 'company data lost'}
        return {'code': 1, 'data': res, 'c_data': c_data, 'msg': 'success'}
    except Exception as e:
        print(e)
        return {'code': 0, 'data': None, 'msg': 'server error'}


@tw_router.post('/eps_record')
async def create_eps(body: EPSBody,
                     db=Depends(mongoClient)):
    model = db.eps
    item = body.__dict__
    try:
        await model.insert_one(item)
        return {'code': 1, 'data': None, 'msg': 'insert success'}
    except:
        return {'code': 0, 'data': None, 'msg': 'insert failed'}


@tw_router.get('/topHolder/{stock_id}')
async def get_tw_topHolder(stock_id: str = Path(..., pattern='\d+'),
                           db=Depends(mongoClient)):

    max_date = int(pendulum.today(tz='Asia/Taipei').add(months=-1).format('YYYYMM'))
    min_date = int(pendulum.today(tz='Asia/Taipei').add(years=-1).add(months=-1).format('YYYYMM'))
    data = db.topHolder.find({'stock_id': stock_id,'date': {'$gte': min_date, '$lte': max_date}},
                               {'_id': 0}).sort([('date', 1)])
    x_list, y1_list, y2_list, y3_list, y4_list = list(), list(), list(), list(), list()
    async for r in data:
        x_list.append(str(r['date']))
        y1_list.append(Decimal(str(round(r.get('directors_hr', 0), 2))))
        y2_list.append(Decimal(str(round(r.get('managers_hr', 0), 2))))
        y3_list.append(Decimal(str(round(r.get('directors_pr', 0), 2))))
        y4_list.append(Decimal(str(round(r.get('managers_pr', 0), 2))))
    if not x_list:
        x_list = [0] * 5
        y1_list = [0] * 5
        y2_list = [0] * 5
        y3_list = [0] * 5
        y4_list = [0] * 5
    chart = TopHolderLine(title='董監經理人持股趨勢', x=x_list, y1=y1_list, y2=y2_list, y3=y3_list, y4=y4_list, y1_name='董監HR', y2_name='經理HR', y3_name='董監PR', y4_name='經理PR')
    return chart.dump_options_with_quotes()


@tw_router.get('/holder/{stock_id}')
async def get_tw_holderData(stock_id: str = Path(..., pattern='\d+'),
                         db=Depends(mongoClient)):
    print(stock_id)
    data = db.holder.find({'stock_id': stock_id}, {'_id': 0}).sort([('date', 1)])
    x_data, y1_data, y2_data = list(), list(), list()
    async for d in data:
        x_data.append(d['date'])
        y1_data.append(d['holder400'])
        y2_data.append(d['holder1000'])

    chart = HolderLine(title='持股人趨勢', x=x_data, y1=y1_data, y2=y2_data, y1_name='400張%', y2_name='1000張%')
    return chart.dump_options_with_quotes()


@tw_router.get('/jer/{stock_id}')
async def get_tw_jer(
        stock_id: str = Path(..., pattern='\d+'),
        db=Depends(mongoClient)
):
    stock = await db.company2.find_one({'stock_id': stock_id}, {'nickname': 1,'employees': 1})
    if not stock:
        return {}
    nickname = stock.get('nickname', '')
    emps = stock.get('employees', 0)
    global_title = f'{nickname}:{stock_id}:{emps}人'
    stock_data = db.companydata.find({'stock_id': stock_id},
                                     {'jer_max': 1, 'jer_min': 1, 'jer_full_min': 1, 'jer_full_max': 1, 'date': 1,
                                      'differenceSetCount': 1,
                                      'jobOffCount': 1, }).sort([('date', 1)])
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
        jer_f_max.append(s.get('jer_full_max', 0))
        jer_f_min.append(s.get('jer_full_min', 0))
        differ_set.append(s['differenceSetCount'])
        job_offs.append(s['jobOffCount'])

    bar = stockChart(date_arr, jer_min, jer_max, jer_f_min, jer_f_max, differ_set, job_offs, global_title)
    return bar.dump_options_with_quotes()