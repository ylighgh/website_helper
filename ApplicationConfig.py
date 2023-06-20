#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from happy_python import HappyConfigBase


class ApplicationConfig(HappyConfigBase):
    def __init__(self):
        super().__init__()

        self.section = 'ChinaKaoYan'
        self.cookie = ''
        self.cky_html_directory = ''
        self.cky_index_html = ''
