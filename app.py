#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import argparse
import string
import threading
import csv
import hashlib
import os
import shutil
import time
import re
from datetime import datetime, timedelta
import random

import requests
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from utils import MetaData
from bs4 import BeautifulSoup
from happy_python import dict_to_pretty_json, HappyPyException, str_to_dict, dict_to_str
from happy_python.happy_log import HappyLogLevel
from requests import Response
from utils import gen_html
from utils import get_request_headers, get_request_body, get_domain

from common import hlog, config, headers, cookies

hlog = hlog

DOMAIN = ""
table_data = []
question_code = ""
current_datetime = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
line_number = 0

total_requests = 0
successful_requests = 0
failed_requests = 0
total_time: datetime
url_status_dict = dict()
semaphore = threading.Semaphore(10)

# 查询变量
COLLEGE_ID = 0


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"


class CsvRow:
    serial_number: str
    header_1_title: str
    header_2_title: str
    header_3_title: str
    header_4_title: str
    link_title: str
    request_method: str
    request_uri: str
    except_response_code: str
    request_body: str
    request_body_attachment: str

    def __init__(self, serial_number: str,
                 header_1_title: str,
                 header_2_title: str,
                 header_3_title: str,
                 header_4_title: str,
                 link_title: str,
                 request_method: str,
                 request_uri: str,
                 except_response_code: str,
                 request_body: str,
                 request_body_attachment: str):
        self.serial_number = serial_number
        self.header_1_title = header_1_title
        self.header_2_title = header_2_title
        self.header_3_title = header_3_title
        self.header_4_title = header_4_title
        self.link_title = link_title
        self.request_method = request_method
        self.request_uri = request_uri
        self.except_response_code = except_response_code
        self.request_body = request_body
        self.request_body_attachment = request_body_attachment


class ColInfo(Enum):
    SerialNumber = '编号'
    Header1Title = '1级标题'
    Header2Title = '2级标题'
    Header3Title = '3级标题'
    Header4Title = '4级标题'
    LinkTitle = '链接标题'
    RequestMethod = 'HTTP方法'
    RequestURI = 'URI'
    ExceptResponseCode = 'HTTP代码'
    RequestBody = '载荷'
    RequestBodyAttachment = '附件'


class RowHandler:
    @staticmethod
    def get_handler(row: CsvRow):
        global line_number, response
        global failed_requests
        global successful_requests
        line_number = row.serial_number
        url = DOMAIN + row.request_uri
        hlog.info("编号: %s,正在请求: %s,请求方式: %s" % (row.serial_number, url, row.request_method))
        try:
            if 'h.chinakaoyan.com' in url:
                response = requests.get(url, headers=headers, cookies=cookies)
                # get_college_id(url, response)
            else:
                response = requests.get(url, headers=headers)
            if response.status_code != 200:
                failed_requests += 1
                return response
        except Exception as e:
            hlog.error("URL: %s, 请求失败,错误信息: %s" % (url, e))
            failed_requests += 1
            return response
        else:
            successful_requests += 1
            return response

    @staticmethod
    def post_handler(row: CsvRow):
        global line_number, response
        global failed_requests
        global successful_requests
        files = None
        line_number = row.serial_number

        url = DOMAIN + row.request_uri

        data = get_request_body(row.request_body)
        post_headers = get_request_headers(url, data.content_type)

        if row.request_body_attachment != 'NULL':
            files = get_requests_body_attachment(row.request_body_attachment)

        hlog.info("编号: %s,正在请求: %s,请求方式: %s" % (row.serial_number, url, row.request_method))
        try:
            response = requests.post(url, headers=post_headers, data=data, cookies=cookies, files=files)
            if response.status_code != 200:
                failed_requests += 1
                return response
        except Exception as e:
            hlog.error("URL: %s, 请求失败,错误信息: %s" % (url, e))
            failed_requests += 1
            return response
        else:
            successful_requests += 1
            return response


class UrlStatus:
    row_id: int
    row: CsvRow
    resp: Response
    status: int

    def __init__(self, row_id, row, resp=None, status=0) -> None:
        self.row_id = row_id
        self.row = row
        self.resp = resp
        self.status = status


# 每种模式的行处理函数
ROW_HANDLER_MAP = {
    RequestMethod.GET: RowHandler.get_handler,
    RequestMethod.POST: RowHandler.post_handler,
}

# 列数量
COL_SIZE = len(ColInfo)


def generate_random_string():
    res = ''.join(random.choices(string.ascii_lowercase +
                                 string.digits, k=5))

    return str(res)


def generate_hash(data, algorithm='sha256'):
    hash_object = hashlib.new(algorithm)
    hash_object.update(data.encode('utf-8'))
    hash_value = hash_object.hexdigest()
    return hash_value


def save_response_body(row_id: int, res_body: Response):
    global table_data
    uri = urlparse(res_body.url).path

    # get_verify_code(uri, res_body)

    # 获取当前时间戳
    random_str = generate_random_string()

    www = Path(config.cky_html_directory + current_datetime)

    www.mkdir(exist_ok=True, parents=True)

    dirname = str(www) + uri
    file_store_path = Path(dirname)

    # 不存在则创建,存在则添加时间戳
    if not file_store_path.exists():
        file_store_path.mkdir(exist_ok=True, parents=True)
    else:
        base_filename, ext = os.path.splitext(str(file_store_path))
        dirname = f"{base_filename}_{random_str}{ext}"
        file_store_path = Path(dirname)
        file_store_path.mkdir(exist_ok=True, parents=True)

    filename_body = os.path.join(file_store_path, 'body.txt')
    filename_request_header = os.path.join(file_store_path, 'request_headers.json')
    filename_response_header = os.path.join(file_store_path, 'response_headers.json')

    with open(filename_request_header, 'w', encoding='UTF-8') as f:
        f.write(dict_to_str(dict(res_body.request.headers)))

    with open(filename_response_header, 'w', encoding='UTF-8') as f:
        f.write(dict_to_str(dict(res_body.headers)))

    with open(filename_body, 'w', encoding='UTF-8') as f:
        f.write(res_body.text.replace('gb2312', 'utf-8'))

    table_data.append(
        [row_id, res_body.url, res_body.request.method, res_body.status_code,
         round(res_body.elapsed.total_seconds(), 3),
         filename_request_header.replace('var/www/' + current_datetime + '/', ''),
         filename_response_header.replace('var/www/' + current_datetime + '/', ''),
         filename_body.replace('var/www/' + current_datetime + '/', '')])


def get_college_id(url: str, response: Response):
    global COLLEGE_ID
    if '/admin2m0GHi12MA12ge/module/index.php?school=%CB%C4%B4%A8%CA%A6%B7%B6&college=&act=list&module=college' \
       '&Submit3=%CC%E1%BD%BB' in url:
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到所有带有onclick属性的a标签
        a_tags = soup.find_all('a', attrs={'onclick': True})

        # 遍历a标签，提取包含特定文字的id
        for a_tag in a_tags:
            onclick_value = a_tag['onclick']
            if 'test' in onclick_value and '删除学院' in onclick_value:
                href_value = a_tag['href']
                id_match = re.search(r'id=(\d+)', href_value)
                if id_match:
                    college_id = id_match.group(1)
                    # print('学院ID:', college_id)


def get_verify_code(uri: str, response: Response):
    global question_code
    if uri == '/user/ask.shtml' and response.request.method == 'GET':
        soup = BeautifulSoup(response.text, 'html.parser')
        input_tag = soup.find('input', {'name': 'questioncode'})
        question_text = input_tag.find_next(string=True).strip()
        print('验证码问题: ' + question_text)
        question_answer = input("请输入验证码:")
        question_code = question_answer.encode('gbk')


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

    serial_number = row[0]
    header_1_title = row[1]
    header_2_title = row[2]
    header_3_title = row[3]
    header_4_title = row[4]
    link_title = row[5]
    request_method = row[6]
    uri = row[7]
    except_response_code = row[8]
    request_body = row[9]
    request_body_attachment = row[10]

    if len(row) != COL_SIZE:
        raise HappyPyException('数组%s的数量不正确，应该有%d个元素' % (row, COL_SIZE))
    csv_row = CsvRow(serial_number, header_1_title, header_2_title, header_3_title, header_4_title,
                     link_title, request_method, uri, except_response_code, request_body, request_body_attachment)

    return csv_row


def process_url(url, row):
    handler = ROW_HANDLER_MAP.get(RequestMethod[row.request_method])
    resp = handler(row)
    # 修改 URL 状态为已访问
    url.status = 1
    url.resp = resp
    # 释放信号量
    semaphore.release()


def parse_csv_file(csv_file: str):
    global total_requests
    global total_time
    try:
        with open(csv_file, encoding='UTF-8', mode='r') as f:
            try:
                reader = csv.reader(f)

                # 跳过标题行
                next(reader)

                # 建立字典
                for row in reader:
                    row_obj = to_csv_row_obj(row)
                    url_status_dict[generate_hash(row_obj.serial_number)] = UrlStatus(row_obj.serial_number, row_obj)

                total_requests = len(url_status_dict)

                # 基于字典请求url
                start_time = time.time()

                threads = []
                for k, v in url_status_dict.items():
                    if v.status == 0:
                        # 获取信号量，控制并发数量
                        semaphore.acquire()
                        t = threading.Thread(target=process_url, args=(v, v.row))
                        threads.append(t)
                        t.start()

                # 等待所有线程完成
                for t in threads:
                    t.join()

                end_time = time.time()
                total_time = end_time - start_time
                total_time = str(timedelta(seconds=round(total_time)))
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
    DOMAIN = get_domain(args.domain)
    hlog.set_level(args.log_level)

    try:
        # check_cookie_is_expired(config.mobilephone, config.password)
        parse_csv_file(args.csv_file)
        total_response_time = 0
        for k, v in url_status_dict.items():
            if v.resp is not None:
                total_response_time += round(v.resp.elapsed.total_seconds(), 3)
            else:
                total_response_time += 0
            save_response_body(v.row_id, v.resp)
        avg_response_time = round(total_response_time / total_requests, 3)
        save_position = config.cky_index_html.replace('${current_datetime}', current_datetime)
        gen_html(save_position, table_data,
                 MetaData(total_requests, successful_requests, failed_requests, avg_response_time,
                          total_time))
        hlog.info("网页保存位置: %s" % save_position)
        shutil.copy('v2.csv', f'var/www/{current_datetime}/{current_datetime}.csv')
    except HappyPyException as e:
        hlog.error(e)
        exit(1)


if __name__ == '__main__':
    main()
