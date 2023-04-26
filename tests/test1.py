#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import urllib.parse

import requests
from bs4 import BeautifulSoup
from happy_python import str_to_dict

headers = {'User-Agent': 'GeekCampBot/1.0'}


def get_cookie_from_cache():
    with open('../var/cache/cookie/cky.cache', encoding='UTF-8', mode='r') as f:
        cookie = f.read()

    return str_to_dict(cookie)


def main():
    response = requests.get('https://www.chinakaoyan.com/user/ask.shtml', cookies=get_cookie_from_cache(),
                            headers=headers)

    soup = BeautifulSoup(response.text, 'html.parser')
    input_tag = soup.find('input', {'name': 'questioncode'})
    question_text = input_tag.find_next(string=True).strip()
    print('验证码问题: ' + question_text)
    question_answer = input("请输入验证码:")
    unicode_str = question_answer.encode('gbk')

    data = {
        "title": "测试post",
        "question": "测试post",
        "ClassLevel1": 7,
        "ClassLevel2": 21,
        "province": "",
        "schoolId": "",
        "subType": "",
        "specialityId": "",
        "mpn": 0,
        "questioncode": unicode_str
    }

    response_post = requests.post('https://www.chinakaoyan.com/user/ask.shtml', cookies=get_cookie_from_cache(),
                                  headers=headers, data=data)

    print(response_post.text)
    print(response_post.status_code)


if __name__ == '__main__':
    main()
