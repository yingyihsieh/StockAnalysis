import os

HOST = '0.0.0.0'
PORT = 8888
STATIC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
FILE_PATH = os.path.join(STATIC_PATH, 'files')


class MessageContent:
    def __init__(self):
        self.content = ''


msg_content = MessageContent()