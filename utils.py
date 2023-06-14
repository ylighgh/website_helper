#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from datetime import datetime


class MetaData:
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: datetime
    avg_response_time: float

    def __init__(self, total_requests_count, successful_requests_count, failed_requests_count, avg_response_time,total_time_count):
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
        for i, cell in enumerate(row):
            if i == 5 or i == 6 or i == 7:
                row_content += f'<td><a href="{cell}">{cell}</a></td>'
            elif i == 3 and cell != 200:
                row_content += f'<td style="color: red;">{cell}错误</td>'
            elif i == 1:
                row_content += f'<td><a href="{cell}">{cell}</a></td>'
            else:
                row_content += f'<td>{cell}</td>'
        table_content += f'<tr>{row_content}</tr>'

    body_content = gen_html_body(table_content, metadata)

    with open(filename, "w") as f:
        f.write(body_content)
