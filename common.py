#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from pathlib import PurePath
from happy_python import HappyConfigParser, HappyLog, str_to_dict
from ApplicationConfig import ApplicationConfig

CONFIG_DIR = PurePath(__file__).parent / 'configs'
CONFIG_FILENAME = str(CONFIG_DIR / 'application.ini')

config = ApplicationConfig()
HappyConfigParser.load(CONFIG_FILENAME, config)
hlog = HappyLog.get_instance()

headers = {'User-Agent': 'GeekCamp/1.0'}

with open(config.cookie, mode='r', encoding='utf-8') as f:
    cookies = str_to_dict(f.read())

