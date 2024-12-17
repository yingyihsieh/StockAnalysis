# -*- coding: utf-8 -*-
# @Time : 2024/5/22  15:11
# @Author : Andy Hsieh
# @Desc :
import requests
import pendulum



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


