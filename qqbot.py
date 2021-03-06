from os import path

import nonebot

import config
import logging
from nonebot.log import logger


if __name__ == '__main__':
    nonebot.init(config)
    #logger.setLevel(logging.WARNING)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'awesome', 'plugins'),
        'awesome.plugins'
    )
    nonebot.run(host='127.0.0.1', port=8080)
