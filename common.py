#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from pathlib import PurePath
from happy_python import HappyConfigParser, HappyLog
from ApplicationConfig import ApplicationConfig

CONFIG_DIR = PurePath(__file__).parent / 'configs'
CONFIG_FILENAME = str(CONFIG_DIR / 'application.ini')

config = ApplicationConfig()
HappyConfigParser.load(CONFIG_FILENAME, config)
hlog = HappyLog.get_instance()

headers = {'User-Agent': 'GeekCampBot/1.0'}
