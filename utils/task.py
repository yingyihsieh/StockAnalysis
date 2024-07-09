# -*- coding: utf-8 -*-
# @Time : 2024/5/22  14:20
# @Author : Andy Hsieh
# @Desc :

import os
import time
import requests
import pendulum
import pymongo
import pandas as pd
from bs4 import BeautifulSoup
from settings import PORT, FILE_PATH, MONGOURI


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
    client = pymongo.MongoClient(MONGOURI)
    db = client.finance
    return db


def world_finance_task():
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
    db = get_model()
    model = db.world_stock
    model.update_one({'date': data['date']},
                     {'$set': data},
                     upsert=True)
    time.sleep(0.1)
    wf_notify()


class UpdateYoY:
    def __init__(self):
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.url = 'https://mops.twse.com.tw/server-java/FileDownLoad'
        self.date = pendulum.today(tz='Asia/Taipei').add(months=-1)
        self.keys = ['sii', 'otc']
        self.client = pymongo.MongoClient('mongodb://192.168.10.67:27017')
        self.db = self.client.finance
        self.model = self.db.company2

    def date_format(self):
        print('target dt = ', self.date)
        cy = str(self.date.year - 1911)
        cm = f'{self.date.month}'
        wy = str(self.date.year)
        wm = f'{self.date.month}' if self.date.month > 9 else f'0{self.date.month}'
        print(f'cy = {cy}, cm = {cm}, wy = {wy}, wm = {wm}')
        return cy, cm, wy, wm

    def spider(self, year, month, index, file):
        form = {
            'step': '9',
            'functionName': 'show_file2',
            'filePath': f'/t21/{index}/',
            'fileName': f't21sc03_{year}_{month}.csv'
        }
        resp = requests.post(url=self.url, headers=self.headers, data=form)
        data = resp.content
        print(file)
        with open(file, 'wb') as f:
            f.write(data)


    def parse(self, file, west_yr, west_mn):
        df = pd.read_csv(file)
        df = df.fillna('0')
        data = df.to_dict(orient='records')

        reason_map = {str(d['公司代號']): {
            'remark': d['備註'].replace('-', ''),
            'mom': round(float(d["營業收入-上月比較增減(%)"]), 2),
            'yoy': round(float(d["營業收入-去年同月增減(%)"]), 2)
        } for d in data}


        for s in reason_map:
            print('update now = ', s)

            item = self.model.find_one({'stock_id': s}, {'_id': 1, 'stock_id': 1, 'updated': 1,
                                                         'yoy-1': 1, 'yoy-2': 1, 'yoy-3': 1,
                                                         'yoy-4': 1, 'yoy-5': 1, 'yoy-6': 1,
                                                         'mom-1': 1, 'mom-2': 1, 'mom-3': 1,
                                                         'mom-4': 1, 'mom-5': 1, 'mom-6': 1})

            time.sleep(0.1)
            if not item:
                continue
            if item['updated'] == f'{west_yr}{west_mn}':
                continue
            print('updated==', s)
            if item['yoy-1'] == '':
                item['yoy-1'] = '0'
            if item['yoy-2'] == '':
                item['yoy-2'] = '0'
            if item['yoy-3'] == '':
                item['yoy-3'] = '0'
            if item['yoy-4'] == '':
                item['yoy-4'] = '0'
            if item['yoy-5'] == '':
                item['yoy-5'] = '0'
            if item['mom-1'] == '':
                item['mom-1'] = '0'
            if item['mom-2'] == '':
                item['mom-2'] = '0'
            if item['mom-3'] == '':
                item['mom-3'] = '0'
            if item['mom-4'] == '':
                item['mom-4'] = '0'
            if item['mom-5'] == '':
                item['mom-5'] = '0'

            updated_item = {
                                 'remark': f'{west_yr}/{west_mn} ' + reason_map[s]['remark'],
                                 'updated': f'{west_yr}{west_mn}',
                                 'yoy-1': reason_map[s]['yoy'],
                                 'yoy-2': round(float(item['yoy-1']), 2),
                                 'yoy-3': round(float(item['yoy-2']), 2),
                                 'yoy-4': round(float(item['yoy-3']), 2),
                                 'yoy-5': round(float(item['yoy-4']), 2),
                                 'yoy-6': round(float(item['yoy-5']), 2),
                                 'mom-1': reason_map[s]['mom'],
                                 'mom-2': round(float(item['mom-1']), 2),
                                 'mom-3': round(float(item['mom-1']), 2),
                                 'mom-4': round(float(item['mom-1']), 2),
                                 'mom-5': round(float(item['mom-1']), 2),
                                 'mom-6': round(float(item['mom-1']), 2)
                             }
            self.model.update_one({'stock_id': s},
                                  {'$set': updated_item})


    def income_notify(self):
        content = '營收已更新'
        url = f'http://127.0.0.1:{PORT}/message?content={content}'
        resp = requests.post(url=url)
        print(resp.json())


    def run(self):
        cyear, cmonth, wyear, wmonth = self.date_format()
        for k in self.keys:
            file_path = os.path.join(FILE_PATH, f'{k}_{cyear}_{cmonth}.csv')
            self.spider(cyear, cmonth, k, file_path)
            time.sleep(2)
            self.parse(file_path, wyear, wmonth)
        self.income_notify()
        time.sleep(1)
        self.client.close()


def income_task():
    if not os.path.exists(FILE_PATH):
        os.mkdir(FILE_PATH)
    obj = UpdateYoY()
    obj.run()
