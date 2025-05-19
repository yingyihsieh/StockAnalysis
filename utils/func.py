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






def list_to_nested_dict(data, keys=['quantity', 'og_size', 'pack']):
    nested_dict = {}
    og_size_set = set()
    quantity_set = set()
    for item in data:
        current_level = nested_dict
        for key in keys:
            if item[key] not in current_level:
                if key == 'quantity': quantity_set.add(item[key])
                if key == 'og_size': og_size_set.add(item[key])
                current_level[item[key]] = dict()

            current_level = current_level[item[key]]
        last_key = keys[-1]
        if last_key in item:

            current_level[item[keys[-1]]] = {
                'size': item['size'],
                'weight': item['weight'],
                'price': item['price']
            }
    return nested_dict, list(quantity_set), list(og_size_set)