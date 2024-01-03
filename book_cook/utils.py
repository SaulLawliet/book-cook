import hashlib
import os
import random
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
}

# BookCook instance
BC = None

# BookCook IE
IE = None


def get_cache_filename(filename):
    dir = f'_cache/{IE.ie_key()}/'
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir + filename


def _http_get(url, headers=_HEADERS):
    if BC.params['sleep_seconds']:
        seconds = BC.params['sleep_seconds']
        step = max(int(seconds * 0.3), 3)
        sleep = random.randint(seconds, seconds + step)
        print(f'开启了请求限流, 本次暂停{sleep}s.')
        time.sleep(sleep)

    return requests.get(url, headers=headers)


def http_get_content(url, allow_cache=False, headers=_HEADERS):
    return http_get_content_full_info(url, allow_cache, headers)[0]


def http_get_content_full_info(url, allow_cache=False, headers=_HEADERS):
    """return: body, md5, file_type"""

    file_type = None
    filename = url.split('?')[0].split('/')[-1]
    if '.' in filename:
        file_type = filename.split('.')[-1]

    md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_file = get_cache_filename(md5)
    if file_type is not None:
        cache_file += '.' + file_type

    html = ''
    if allow_cache and os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            html = f.read()
            print('from cache: ' + url + ' < ' + cache_file)
    else:
        resp = _http_get(url, headers=headers)
        if resp.status_code != 200:
            print(url, 'STATUS:', resp.status_code)
        else:
            html = resp.content
            if allow_cache:
                with open(cache_file, 'wb') as f:
                    f.write(html)
                print('from http: ' + url + ' > ' + cache_file)
            else:
                print('from http: ' + url)
    return html, md5, file_type


def url_to_bs(url, allow_cache=False, headers=_HEADERS):
    return BeautifulSoup(http_get_content(url, allow_cache=allow_cache, headers=headers), 'html.parser')


def str_to_bs(content):
    return BeautifulSoup(content, 'html.parser')


def parse_txt(lines, chapter_flag, skip_head=0, skip_tail=0):
    """将txt切割成不同章节, TODO: 适配更多类型, 需要样本"""
    if type(lines) == str:
        lines = re.split('\r\n|\n', lines)
    if skip_head > 0:
        lines = lines[skip_head:]

    if skip_tail > 0:
        lines = lines[:-skip_tail]

    chapter_flag_re = re.compile(chapter_flag)
    chapters = []
    last_chapter = None
    for line in lines:
        if len(line.strip()) == 0:
            continue
        # ValueError: All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters
        # https://stackoverflow.com/a/25920392
        line = re.sub(
            u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', line)

        if chapter_flag_re.match(line.lstrip()):
            # 尝试跳过一些空章节
            if last_chapter and len(last_chapter['content']) <= 1:
                chapters.pop()
            last_chapter = {'title': line, 'content': [f'<h3>{line}</h3>']}
            chapters.append(last_chapter)
        else:
            if last_chapter:
                last_chapter['content'].append(line.replace('  ', '　'))

    for chapter in chapters:
        chapter['content'] = '<br>'.join(chapter['content'])

    return chapters


def read_file(path):
    with open(path) as f:
        return f.read()


def write_string(s, out=None):
    if out is None:
        out = sys.stderr
    out.write(s)
    out.flush()


def split_list(list, step):
    """将list变成等长的多个数组"""
    return [list[i:i+step] for i in range(0, len(list), step)]
