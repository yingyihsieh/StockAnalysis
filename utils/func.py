# -*- coding: utf-8 -*-
# @Time : 2024/5/22  15:11
# @Author : Andy Hsieh
# @Desc :
import random
import time

import requests
import pendulum
import threading
from decimal import Decimal


class MyThread(threading.Thread):
    def __init__(self, func, args):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None


def tsFormat(ts):
    return pendulum.from_timestamp(ts, tz='Asia/Taipei').format('YYYY/MM/DD')


async def demo_requests(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    async with aiohttp.ClientSession() as req:
        resp = await req.get(url=url, headers=headers)
        resp_data = await resp.text()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp_data, 'html.parser')
        title = soup.title.string
    return title


def get_billable_weight_estimator(token, length, width, height, weight, quantity, pack):
    '''pack_map = {
        'box': 1,
        'Bubble Mailer': 2,
        'Poly Mailer': 3,
        'Poster Tube': 5,
        'Bookfold - Large': 7,
        'Ship in Own': 8
    }'''
    url = 'https://packageselection.shipbob.com/api/packageCalc/GetBestPackages'
    payload = {
        "FulfillmentCenterId": 9,
        "CountryISO": "US",
        "UserId": 245753,
        "OrderTypeId": 1,
        "OrderItems": [{"Length": length, "Width": width, "Height": height, "WeightOz": weight, "PackType": pack,
                        "Quantity": quantity, "IsCubiscanned": True}]
    }
    headers = {
        'authorization': f'Bearer {token}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    resp = requests.post(url=url, headers=headers, json=payload)
    resp_data = resp.json()
    print(resp_data)
    try:
        res_str = f"{resp_data['shipBobBox']['domesticBillableWeight']}oz,{resp_data['shipBobBox']['packageName'].split('-')[-1].strip()}"

    except:
        res_str = f"0oz,0x0x0"
    print(res_str)
    return res_str


def mcf_spider(l, w, h, weight):
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://supplychain.amazon.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://supplychain.amazon.com/pricing',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    json_data = {
        'shipmentItems': [
            {
                'dimensions': {
                    'packageHeight': h,
                    'packageWidth': w,
                    'packageLength': l,
                    'packageWeight': weight,
                    'dimensionUnit': 'in',
                    'weightUnit': 'lb',
                },
                'unitsPerOrder': 1,
                'shippingSpeed': 'Standard',
            },
        ],
        'program': 'mcf',
    }

    response = requests.post(
        'https://supplychain.amazon.com/api/pricing/estimateFees',
        headers=headers,
        json=json_data,
    )
    try:
        res = response.json()
        for i in res['estimatedFees']:
            if i['name'] == 'FulfillmentFee':
                return Decimal(str(i['amount']['Value']))
        return 0
    except Exception as e:
        print('amazon spider=', e)
        return 0


def get_mcf(item_list):
    def bits_method(num: Decimal):
        s_num = str(num)
        print('s_num=', s_num)
        if '.' in s_num:
            v, f = s_num.split('.')
            if len(f) > 2 and int(f[2]) > 4:
                return Decimal(v) + Decimal(f'0.{f[0]}{f[1]}') + Decimal('0.01')
            else:
                return Decimal(v) + Decimal(f'0.{f}')
        return num

    print('T: itemlist', item_list)
    result = list()
    for info in item_list:
        w, v = info.split(',')
        print(f'T: w={w}, v={v}')
        length, width, height = v.strip().split('x')
        w = w.strip().replace('oz', '')
        print(f'T: w={w}, v={length} {width} {height}')
        weight = str(bits_method(Decimal(w) / Decimal('16')))
        print(f'weight=', weight)
        result.append(mcf_spider(length, width, height, weight))
        time.sleep(random.uniform(0.5, 1.1))
    return result