# -*- coding: utf-8 -*-
# @Time : 2024/5/20  17:42
# @Author : Andy Hsieh
# @Desc :

import uvicorn
from winApp import create_app


app = create_app()


if __name__ == '__main__':
    uvicorn.run(app='manage:app', host='0.0.0.0', port=5000, reload=True)
