# -*- coding: utf-8 -*-
# @Time : 2024/5/20  17:50
# @Author : Andy Hsieh
# @Desc :

import time
import hashlib
import pendulum
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Depends, Query, Path
from fastapi.requests import Request
from requestBody import GroupBody, NewsTaskBody, NoteBody, GroupItemBody
from database import mongoClient, redisClient
from charts.cn import jer_chart


cn_router = APIRouter()
templates = Jinja2Templates(directory='templates')



@cn_router.post('/groups')
async def create_cn_group(body: GroupBody,
                          db=Depends(mongoClient)):
    try:
        model = db.cn_group
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


@cn_router.get('/groups/list')
async def get_cn_groups(task:bool = Query(default=False),
                        db=Depends(mongoClient)):
    try:
        groups = db.cn_group.find({}, {'_id': 0})
        htmlList = list()
        async for g in groups:
            if task:
                html = f'''
                <div style = "margin-bottom: 5px;text-align: center">
                    <button task_id = "{g['uid']}" type = "button" class ="btn-lg btn-primary" style="width: 80%" onclick="startCnEvent(this)">{g['title']}</button>
                </div>
                '''
            else:
                html = f'<li class="list-group-item" id="{g["uid"]}">{g["title"]}</li>'
            htmlList.append(html)
        content = '\n'.join(htmlList)
        return {'code': 1, 'data': content, 'msg': 'success'}
    except:
        return {'code': 0, 'data': None, 'msg': '未知錯誤'}


@cn_router.get('/groups/choice_list')
async def get_cn_gp_choice_list(db=Depends(mongoClient)):
    try:
        groups = db.cn_group.find({}, {'_id': 0})
        htmlList = list()
        async for g in groups:
            html = f'<option value="{g["uid"]}">{g["title"]}</option>'
            htmlList.append(html)
        content = '\n'.join(htmlList)
        return {'code': 1, 'data': content, 'msg': 'success'}
    except:
        return {'code': 0, 'data': None, 'msg': '未知錯誤'}


@cn_router.post('/groupItem')
async def add_groupList(body: GroupItemBody,
                        db=Depends(mongoClient)):
    try:
        item = {
            'stock_id': body.stock_id,
            'stock_nickname': body.stock_nickname,
            'group_id': body.group_id
        }

        target = await db.cn_groupDetail.find_one({'group_id': item['group_id'], 'stock_id': body.stock_id})
        if target:
            return {'code': 0, 'data': None, 'msg': '請勿重複添加'}
        await db.cn_groupDetail.insert_one(item)


        msg = f'{body.stock_nickname} 股票代號 {body.stock_id} 加入 {body.group_name} 成功!'
        return {'code': 1, 'data': None, 'msg': msg}
    except Exception as e:
        print('add groupList error', e)
        return {'code': 0, 'data': None, 'msg': '系統錯誤'}


@cn_router.delete('/groupItem')
async def add_groupList(stock_id: str=Query(...),
                        group_id: str=Query(...),
                        db=Depends(mongoClient)):
    try:

        await db.cn_groupDetail.delete_one({'group_id': group_id, 'stock_id': stock_id})

        return {'code': 1, 'data': None, 'msg': 'delete success'}
    except Exception as e:
        print('add groupList error', e)
        return {'code': 0, 'data': None, 'msg': 'something wrong'}


@cn_router.post('/addTask')
async def add_cnNewsTask(body: NewsTaskBody,
                         rdb=Depends(redisClient)):
    try:
        item = {'uid': body.uid, 'loc': 'cn'}
        await rdb.rpush('news_task', str(item))
        return {'code': 1, 'data': None, 'msg': '任務已啟動'}
    except:
        return {'code': 0, 'data': None, 'msg': '任務啟動失敗'}



@cn_router.get('/company/list')
async def get_cn_company(request: Request,
                      stock_id: str = Query(default=''),
                      page: int = Query(default=1),
                      size: int = Query(default=100),
                      db=Depends(mongoClient)):
    filter = {'stock_id': {'$in': stock_id.split(',')}} if stock_id else dict()
    model = db.cnCompany
    total = await model.count_documents(filter)
    total_page, left = divmod(total, size)
    total_page = total_page if not left else total_page + 1
    queryset = model.find(filter, {'_id': 0, 'title': 1, 'stock_id': 1, 'emps': 1, 'remark': 1}).sort('_id', 1).skip((page - 1) * size).limit(size)
    dataset = [q async for q in queryset]
    return templates.TemplateResponse(
        'cnCompany.html',
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


@cn_router.get('/note')
async def retrieve_cn_note(stock_id: str = Query(...),
                          db=Depends(mongoClient)):
    try:
        data = db.cnNote.find({'stock_id': stock_id}).sort([('_id', -1)]).limit(5)
        html_list = list()
        async for d in data:
            html_str = f'''<li class="list-group-item">{d["note"]}<span class="badge">{d["created"]}</span></li>'''
            html_list.append(html_str)
        html_content = '\n'.join(html_list)
        return {'code': 1, 'data': html_content, 'msg': 'Note success!'}
    except:
        return {'code': 0, 'data': '', 'msg': 'Note fail!'}


@cn_router.post('/note')
async def create_cn_note(body: NoteBody,
                      db=Depends(mongoClient)):
    try:
        note_item = {
            'stock_id': body.stock_id,
            'note': body.note,
            'created': pendulum.now(tz='Asia/Taipei').format('YYYY-MM-DD HH:mm:ss')
        }
        await db.cnNote.insert_one(note_item)
        return {'code': 1, 'data': None, 'msg': 'Note success!'}
    except:
        return {'code': 0, 'data': None, 'msg': 'Note fail!'}


@cn_router.get('/charts/{stock_id}')
async def get_cn_charts(stock_id: str = Path(...),
                        db=Depends(mongoClient)):
    data = db.cnCompanyData.find({'stock_id': stock_id},
                                 {'_id': 0}).sort([('created', -1)]).limit(730)
    data = [d async for d in data]
    x, jer_y, producer_y = list(), list(), list()

    for d in data:
        x.append(d['created'])
        jer_y.append(round(d['JER'], 4) * 100)
        producer_y.append(d['生产/制造/研发'])

    jer_line = jer_chart(x=x, y1=jer_y, y2=producer_y)
    return jer_line.dump_options_with_quotes()


@cn_router.get('/show/{stock_id}')
async def show_chart_page(
        request: Request,
        stock_id: str = Path(...)):
    return templates.TemplateResponse(
        'demo_chart.html',
        {
            'request': request,
            'stock_id': stock_id,
        },
    )