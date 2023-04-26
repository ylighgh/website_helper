#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import argparse
import csv
import os
import time

import requests
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from happy_python import dict_to_pretty_json, HappyPyException, str_to_dict
from happy_python.happy_log import HappyLogLevel
from requests import Response
from utils import gen_html

from common import hlog, config, headers

hlog = hlog
line_number = 0

DOMAIN = 'http://'
table_data = []
question_code = ""


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"


class CsvRow:
    header_1_title: str
    header_2_title: str
    header_3_title: str
    header_4_title: str
    link_title: str
    request_method: str
    uri: str
    request_body: str
    request_body_attachment: str

    def __init__(self,
                 header_1_title: str,
                 header_2_title: str,
                 header_3_title: str,
                 header_4_title: str,
                 link_title: str,
                 request_method: str,
                 uri: str,
                 request_body: str,
                 request_body_attachment: str):
        self.header_1_title = header_1_title
        self.header_2_title = header_2_title
        self.header_3_title = header_3_title
        self.header_4_title = header_4_title
        self.link_title = link_title
        self.request_method = request_method
        self.uri = uri
        self.request_body = request_body
        self.request_body_attachment = request_body_attachment


class ColInfo(Enum):
    Header1Title = '1级标题'
    Header2Title = '2级标题'
    Header3Title = '3级标题'
    Header4Title = '4级标题'
    LinkTitle = '链接标题'
    RequestMethod = '请求方式'
    RequestURI = '请求地址'
    RequestBody = '请求正文'
    RequestBodyAttachment = '请求正文附件'


class RowHandler:
    @staticmethod
    def get_handler(row: CsvRow):
        global line_number
        url = DOMAIN + row.uri
        hlog.info("行号: %s,正在请求: %s,请求方式: %s" % (line_number, url, row.request_method))

        response = requests.get(url, headers=headers, cookies=get_cookie_from_cache())

        save_response_body(response)

    @staticmethod
    def post_handler(row: CsvRow):
        global line_number
        files = None
        url = DOMAIN + row.uri

        data = get_request_body(row.request_body)
        if row.request_body_attachment != 'NULL':
            files = get_requests_body_attachment(row.request_body_attachment)

        hlog.info("行号: %s,正在请求: %s,请求方式: %s" % (line_number, url, row.request_method))

        response = requests.post(url, headers=headers, data=data, cookies=get_cookie_from_cache(), files=files)
        save_response_body(response)


# 每种模式的行处理函数
ROW_HANDLER_MAP = {
    RequestMethod.GET: RowHandler.get_handler,
    RequestMethod.POST: RowHandler.post_handler,
}

# 列数量
COL_SIZE = len(ColInfo)


def save_response_body(response: Response):
    global line_number
    global table_data

    uri = urlparse(response.url).path

    get_verify_code(uri, response)

    # 获取当前时间戳
    timestamp = int(time.time())

    www = Path(config.cky_html_directory)

    if not www.exists():
        www.parent.mkdir(exist_ok=True, parents=True)

    dirname = config.cky_html_directory + 'html' + uri
    file_store_path = Path(dirname)

    # 不存在则创建,存在则添加时间戳
    if not file_store_path.exists():
        file_store_path.mkdir(exist_ok=True, parents=True)
    else:
        base_filename, ext = os.path.splitext(str(file_store_path))
        dirname = f"{base_filename}_{timestamp}{ext}"
        file_store_path = Path(dirname)
        file_store_path.mkdir(exist_ok=True, parents=True)

    filename = os.path.join(file_store_path, 'body')

    with open(filename, 'w', encoding='UTF-8') as f:
        f.write(response.text.replace('gb2312', 'utf-8'))

    table_data.append(
        [line_number, response.url, response.request.method, response.status_code, filename.replace('var/www/', '')])


def get_verify_code(uri: str, response: Response):
    global question_code
    if uri == '/user/ask.shtml' and response.request.method == 'GET':
        soup = BeautifulSoup(response.text, 'html.parser')
        input_tag = soup.find('input', {'name': 'questioncode'})
        question_text = input_tag.find_next(string=True).strip()
        print('验证码问题: ' + question_text)
        question_answer = input("请输入验证码:")
        question_code = question_answer.encode('gbk')


def get_request_body(json_file: str) -> dict:
    global question_code

    with open(json_file, encoding='UTF-8', mode='r') as f:
        file_content = f.read()

    if json_file == 'postdata/提问.json':
        json_data = str_to_dict(file_content)
        json_data['questioncode'] = question_code
    else:
        json_data = str_to_dict(file_content)
    return json_data


def get_requests_body_attachment(json_file: str) -> dict[Any, tuple[Any, bytes, Any]]:
    with open(json_file, 'r') as f:
        file_content = f.read()

    json_data = str_to_dict(file_content)

    with open(json_data['file_path'], 'rb') as f:
        file_data = f.read()

    files = {json_data['name']: (json_data['file_name'], file_data, json_data['mime_type'])}

    return files


def check_cookie_is_expired(mobilephone: str, password_file: str) -> None:
    cookie_file_path = Path(config.cookie_cache)

    # cookie文件不存在的情况
    if not cookie_file_path.exists():
        cookie_file_path.parent.mkdir(exist_ok=True, parents=True)
        gen_cookie_file(mobilephone, password_file)
    # cookie文件存在的情况
    else:
        response = requests.get(f'{DOMAIN}/user/', headers=headers, cookies=get_cookie_from_cache())

        # 在response.text中查找用户id,当获取不到用户id时说明cookie失效,需要重新获取
        if config.user_id not in response.text:
            gen_cookie_file(mobilephone, password_file)


def gen_cookie_file(mobilephone: str, password_file: str) -> None:

    cookie = get_cookie_from_network(mobilephone, password_file)

    with open(config.cookie_cache, mode='w') as f:
        f.write(dict_to_pretty_json(cookie))


def get_cookie_from_network(mobilephone: str, password_file: str) -> dict:

    with open(password_file, mode='r', encoding='UTF-8') as f:
        password = f.readline().strip()

    login_data = {
        'mobilephone': mobilephone,
        'password': password,
        'fromUrl': DOMAIN
    }

    response = requests.post(f'{DOMAIN}/login/login.shtml', headers=headers, data=login_data)

    return requests.utils.dict_from_cookiejar(response.cookies)


def get_cookie_from_cache():
    with open(config.cookie_cache, encoding='UTF-8', mode='r') as f:
        cookie = f.read()

    return str_to_dict(cookie)


def to_csv_row_obj(row: list) -> CsvRow:
    hlog.var('row', row)

    header_1_title = row[0]
    header_2_title = row[1]
    header_3_title = row[2]
    header_4_title = row[3]
    link_title = row[4]
    request_method = row[5]
    uri = row[6]
    request_body = row[7]
    request_body_attachment = row[8]

    if len(row) != COL_SIZE:
        raise HappyPyException('数组%s的数量不正确，应该有%d个元素' % (row, COL_SIZE))

    csv_row = CsvRow(header_1_title, header_2_title, header_3_title, header_4_title,
                     link_title, request_method, uri, request_body, request_body_attachment)

    return csv_row


def parse_csv_file(csv_file: str):
    global line_number
    try:
        with open(csv_file, encoding='UTF-8', mode='r') as f:
            try:
                reader = csv.reader(f)

                # 跳过标题行
                next(reader)

                for row in reader:
                    line_number += 1

                    row_obj = to_csv_row_obj(row)
                    handler = ROW_HANDLER_MAP.get(RequestMethod[row_obj.request_method])
                    handler(row_obj)

                    # time.sleep(1)
                hlog.info("请求结束")
            except csv.Error as e:
                msg = '解析CSV文件行时出现错误\n'
                msg += '%s,%d行: %s' % (csv_file, reader.line_num, e)
                raise HappyPyException(msg)
    except FileExistsError as e:
        msg = '读取文件错误：%s：%s' % (csv_file, e)
        hlog.error(msg)
    except FileNotFoundError as e:
        msg = '文件不存在：%s' % e
        hlog.error(msg)


def main():
    global DOMAIN
    parser = argparse.ArgumentParser(prog='csv_url_visitor',
                                     description='',
                                     usage='%(prog)s -d|-f|-l')

    parser.add_argument('-d',
                        '--domain',
                        help='网站域名',
                        required=True,
                        action='store',
                        dest='domain')

    parser.add_argument('-f',
                        '--file',
                        help='CSV文件',
                        required=True,
                        action='store',
                        dest='csv_file')

    parser.add_argument('-l',
                        '--log-level',
                        help='日志级别，CRITICAL|ERROR|WARNING|INFO|DEBUG|TRACE，默认等级3（INFO）',
                        type=int,
                        choices=HappyLogLevel.get_list(),
                        default=HappyLogLevel.INFO.value,
                        required=False,
                        dest='log_level')

    args = parser.parse_args()
    DOMAIN += args.domain
    hlog.set_level(args.log_level)

    try:
        check_cookie_is_expired(config.mobilephone, config.password)
        parse_csv_file(args.csv_file)
        gen_html(config.cky_index_html, table_data)
    except HappyPyException as e:
        hlog.error(e)
        exit(1)


if __name__ == '__main__':
    main()
