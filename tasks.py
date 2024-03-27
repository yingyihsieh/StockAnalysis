# -*- coding: utf-8 -*-
# @Time : 2024/3/28  上午 02:34
# @Author : Andy Hsieh
# @Desc :


# -*- coding: utf-8 -*-
# @Time : 2023/12/14  下午 12:06
# @Author : Andy Hsieh
# @Desc :

import time
import requests
import pendulum
import pymongo
from bs4 import BeautifulSoup
from settings import PORT


def spider1():
    def parse(soup_, idx):
        table1 = soup_.find_all('table', class_='gvTB')
        rows = table1[idx].find_all('tr')
        target_row = rows[1]
        target_content = target_row.find_all('span')
        content_list = [t.get_text().strip() for t in target_content]

        return content_list
    url = 'https://histock.tw/stock/three.aspx'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    resp = requests.get(url=url, headers=headers)
    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup)
    content_list1 = parse(soup_=soup, idx=0)
    content_list2 = parse(soup_=soup, idx=1)
    print(content_list1[1])
    print(content_list2[1])
    return content_list1[0], content_list1[1], content_list2[1]


def spider2():
    url = 'https://histock.tw/stock/optionthree.aspx'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    resp = requests.get(url=url, headers=headers)
    html = resp.text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='tb-stock tb-option')
    target_content = table.find_all('tr')[2].find_all('span')
    content_list = [t.get_text().strip() for t in target_content]
    return content_list[-7], content_list[-1]


def run_oi():
    _, obs, sfoi = spider1()
    time.sleep(2)
    fioi, pcr = spider2()

    item = {
        'FI-NET': obs,
        'FI-Future-OI': sfoi,
        'FI-Option-OI': fioi,
        'PC-R': pcr,
    }
    return item


def get_us2nt():
    url = 'https://ws.api.cnyes.com/ws/api/v2/universal/quote?type=LMMR'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    resp = requests.get(url=url, headers=headers)
    resp_data = resp.json()
    if resp_data['statusCode'] != 200:
        raise ValueError('spider fail')
    for r in resp_data['data']['items']:
        if r['200009'] == '美元/台幣':
            return {'US/NT': r['6']}


def get_world_index():
    targets = {
        '美元指數': {'成交價':'', '漲幅':''},
        '道瓊指數': {'成交價':'', '漲幅':''},
        'NASDAQ': {'成交價':'','漲幅':''},
        '費城半導體': {'成交價':'','漲幅':''},
        '恆生指數': {'成交價': '', '漲幅': ''},
        '上證指數': {'成交價': '', '漲幅': ''},
        '滬深300': {'成交價': '', '漲幅': ''},
    }
    url = 'https://ws.api.cnyes.com/ws/api/v3/universal/quote?type=IDXMAJOR&column=B&page=1&limit=30'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    resp = requests.get(url=url, headers=headers)
    resp_data = resp.json()
    if resp_data['statusCode'] != 200:
        raise ValueError('spider fail')
    for r in resp_data['data']['items']:
        if r['200009'] in targets:
            targets[r['200009']]['成交價'] = r['6']
            targets[r['200009']]['漲幅'] = r['56']

    results = {
        'USIND': targets['美元指數']['成交價'],
        'USIND△%': targets['美元指數']['漲幅'],
        'DJIA': targets['道瓊指數']['成交價'],
        'DJIA△%': targets['道瓊指數']['漲幅'],
        'NASDAQ': targets['NASDAQ']['成交價'],
        'NASDAQ△%': targets['NASDAQ']['漲幅'],
        'SOX': targets['費城半導體']['成交價'],
        'SOX△%': targets['費城半導體']['漲幅'],
        'HSIND': targets['恆生指數']['成交價'],
        'HSIND△%': targets['恆生指數']['漲幅'],
        'SSEC': targets['上證指數']['成交價'],
        'SSEC△%': targets['上證指數']['漲幅'],
        'CSI300': targets['滬深300']['成交價'],
        'CSI300△%': targets['滬深300']['漲幅'],
    }
    return results


def get_largeTraderFutQry() -> dict:
    date = pendulum.today(tz='America/New_York').format('YYYY/MM/DD')
    url = f'https://www.taifex.com.tw/cht/3/largeTraderFutQry?queryDate={date}&contractId=TX'
    print(url)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }

    resp = requests.post(url=url,headers=headers)
    html = resp.text

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='table_f')
    if not table:
        item = {
            'Top5Position': 0,
            'Top10Position': 0,
        }
        return item
    rows = table.find_all('td', class_='11b')
    data = [r.get_text().strip().replace(',','').replace('\r','').replace('\n','').replace('\t','').replace(' ','').replace('(',';').replace(')','') for r in rows]
    top10res = int(data[23].split(';')[0]) + int(data[17].split(';')[0]) - int(data[13].split(';')[0]) - int(data[27].split(';')[0])
    top5res = int(data[21].split(';')[0]) + int(data[15].split(';')[0]) - int(data[11].split(';')[0]) - int(data[25].split(';')[0])

    item = {
        'Top5Position': top5res,
        'Top10Position': top10res,
    }
    return item


def get_mtx_long2short_ratio():
    url = 'https://ai-all-e25e5ccde503.herokuapp.com/get-sheet-data'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    }
    resp = requests.get(url=url, headers=headers)
    resp_data = resp.json()
    val = resp_data['percentageData'][-1]
    return {'BullBearIND-R': val}


def get_US10YY():
    headers = {
        'origin': 'https://invest.cnyes.com',
        'referer': 'https://invest.cnyes.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }
    url = 'https://ws.api.cnyes.com/ws/api/v1/quote/quotes/GF:US10YY:FUTURES?column=G,QUOTES'
    resp = requests.get(url=url, headers=headers)
    try:
        data = resp.json()
        return {
            'US10Y-Y': data['data'][0]['6'],
            'US10Y-Y△%': round(data['data'][0]['56'], 2)
        }
    except Exception as e:
        print('error=',e)
        raise ValueError('failed')


def wf_notify():
    content = '總經已更新'
    url = f'http://127.0.0.1:{PORT}/message?content={content}'
    resp = requests.post(url=url)
    print(resp.json())


def get_model():
    client = pymongo.MongoClient('mongodb://192.168.10.67:27017')
    db = client.finance
    return db.world_stock


def world_finance():
    print('start req', pendulum.now(tz='America/New_York'))
    keys = ['date', 'US10Y-Y', 'US10Y-Y△%', 'USIND', 'USIND△%', 'DJIA', 'DJIA△%', 'NASDAQ', 'NASDAQ△%', 'SOX', 'SOX△%', 'HSIND','HSIND△%','SSEC','SSEC△%','CSI300','CSI300△%','FI-NET', 'FI-Future-OI', 'FI-Option-OI', 'PC-R', 'US/NT', 'Top5Position', 'Top10Position', 'BullBearIND-R']
    r1 = run_oi()
    time.sleep(0.2)
    r2 = get_us2nt()
    time.sleep(1)
    r3 = get_world_index()
    time.sleep(0.2)
    r4 = get_largeTraderFutQry()
    time.sleep(0.5)
    r5 = get_mtx_long2short_ratio()
    r6 = get_US10YY()
    data = dict()
    print('end req')
    data['date'] = int(pendulum.parse(pendulum.today(tz='America/New_York').format('YYYY-MM-DD'), tz='Asia/Taipei').timestamp())
    data.update(r1)
    data.update(r2)
    data.update(r3)
    data.update(r4)
    data.update(r5)
    data.update(r6)
    data = {k: data[k] for k in keys}
    print('data=', data)
    model = get_model()
    model.update_one({'date': data['date']},
                     {'$set': data},
                     upsert=True)
    time.sleep(0.1)
    wf_notify()




