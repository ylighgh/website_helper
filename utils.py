#!/usr/bin/env python3
# -*- coding:utf-8 -*-

def gen_html_body(table_content: str) -> str:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Index</title>
        <style>
            table {{
                border-collapse: collapse;
                margin: 0 auto;
            }}
            th, td {{
                padding: 10px;
                border: 1px solid black;
                text-align: center;
            }}
            th {{
                background-color: #eee;
            }}
        </style>
    </head>
    <body>
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


def gen_html(filename: str, table_data: list) -> None:
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

    body_content = gen_html_body(table_content)

    with open(filename, "w") as f:
        f.write(body_content)
