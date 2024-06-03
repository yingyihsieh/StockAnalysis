# -*- coding: utf-8 -*-
# @Time : 2024/5/20  17:42
# @Author : Andy Hsieh
# @Desc :
import os

PORT = 8880

MONGOURI = 'mongodb://192.168.10.67:27017'
REDISURI = 'redis://192.168.10.67:6379/15'
# REDISURI = 'redis://127.0.0.1:6379/15'
# MONGOURI = 'mongodb://andy.h:123456@127.0.0.1:27017'



STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')
FILE_PATH = os.path.join(STATIC_PATH, 'files')

class MessageContent:
    def __init__(self):
        self.content = ''


msg_content = MessageContent()
