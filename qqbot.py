from os import path

import nonebot

import config
import logging
from nonebot.log import logger


if __name__ == '__main__':
    nonebot.init(config)
    #logger.setLevel(logging.WARNING)
    print(1)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'awesome', 'plugins'),
        'awesome.plugins'
    )
    nonebot.run(host='172.17.0.1', port=8080)
