# -*- coding: utf-8 -*-
# @Time : 2024/5/22  15:11
# @Author : Andy Hsieh
# @Desc :
import pendulum


def tsFormat(ts):
    return pendulum.from_timestamp(ts, tz='Asia/Taipei').format('YYYY/MM/DD')