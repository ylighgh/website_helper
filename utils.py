#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import random
import string
from datetime import datetime
from urllib.parse import urlparse

from happy_python import str_to_dict
from requests_toolbelt import MultipartEncoder


class MetaData:
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: datetime
    avg_response_time: float

    def __init__(self, total_requests_count, successful_requests_count, failed_requests_count, avg_response_time,
                 total_time_count):
        self.total_time = total_time_count
        self.total_requests = total_requests_count
        self.successful_requests = successful_requests_count
        self.avg_response_time = avg_response_time
        self.failed_requests = failed_requests_count


def gen_html_body(table_content: str, metadata: MetaData) -> str:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>网页检测运行报告</title>
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                background-color: #f2f2f2;
            }}
            h1 {{
                text-align: center;
            }}
            table {{
                border-collapse: collapse;
                margin: 0 auto;
                background-color: #fff;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
            }}
            th, td {{
                padding: 10px;
                border: 1px solid #ddd;
                text-align: center;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            td:first-child {{
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>网页检测运行报告</h1>
        <table>
            <tr>
                <th>总请求数</th>
                <th>成功的请求数</th>
                <th>失败的请求数</th>
                <th>平均响应时间 (秒)</th>
                <th>程序运行时间</th>
            </tr>
            <tr>
                <td>{metadata.total_requests}</td>
                <td>{metadata.successful_requests}</td>
                <td>{metadata.failed_requests}</td>
                <td>{metadata.avg_response_time}</td>
                <td>{metadata.total_time}</td>
            </tr>
        </table>
        <br>
        <table>
            <tr>
                <th>ID</th>
                <th>访问地址</th>
                <th>HTTP请求</th>
                <th>响应代码</th>
                <th>响应时间 (秒)</th>
                <th>请求标头</th>
                <th>响应标头</th>
                <th>响应内容</th>
            </tr>
            {table_content}
        </table>
    </body>
    </html>
    """

    return html


def gen_html(filename: str, table_data: list, metadata: MetaData) -> None:
    table_content = ""

    for row in table_data:
        row_content = ""
        except_response_code = int(row[8])
        row = row[:8]
        for i, cell in enumerate(row):
            if i == 5:
                row_content += f'<td><a href="{cell}">request_headers.json</a></td>'
            elif i == 6:
                row_content += f'<td><a href="{cell}">response_headers.json</a></td>'
            elif i == 7:
                row_content += f'<td><a href="{cell}">response_body.txt</a></td>'
            elif i == 3 and cell != except_response_code:
                row_content += f'<td><text style="color: red;">{cell}错误</text>\n(期望代码：{except_response_code})</td>'
            elif i == 1:
                row_content += f'<td><a href="{cell}">{cell}</a></td>'
            else:
                row_content += f'<td>{cell}</td>'
        table_content += f'<tr>{row_content}</tr>'

    body_content = gen_html_body(table_content, metadata)

    with open(filename, "w") as f:
        f.write(body_content)


def get_request_headers(url: str, content_type: str) -> dict:
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme
    netloc = parsed_url.netloc

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.7',
        'Content-Type': content_type,
        'Host': netloc,
        'Origin': f'{scheme}://{netloc}',
        'Referer': url,
        'User-Agent': 'GeekCamp/1.0',
        'Connection': 'close'
    }

    return headers


def get_request_body(json_file: str):
    with open(json_file, encoding='UTF-8', mode='r') as f:
        file_content = f.read()

    json_data = str_to_dict(file_content)
    boundary = '----WebKitFormBoundary' \
               + ''.join(random.sample(string.ascii_letters + string.digits, 16))

    request_body = MultipartEncoder(fields=json_data, boundary=boundary)

    return request_body


def get_domain(domain: str):
    if domain == 'www.chinakaoyan.com':
        return 'https://www.chinakaoyan.com'
    elif domain == 'h.chinakaoyan.com:8080':
        return 'http://h.chinakaoyan.com:8080'
    else:
        return f'https://{domain}'

# def get_request_body(json_file: str) -> dict:
#     global question_code
#
#     with open(json_file, encoding='UTF-8', mode='r') as f:
#         file_content = f.read()
#
#     json_data = str_to_dict(file_content)
#
#     if 'questioncode' in json_data:
#         json_data['questioncode'] = question_code
#
#     return json_data
