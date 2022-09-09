import hashlib
import os
import requests
from bs4 import BeautifulSoup

_CACHE_DIR = '_cache/'
if not os.path.exists(_CACHE_DIR):
    os.makedirs(_CACHE_DIR)

_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
}


def _http_get(url):
    return requests.get(url, headers=_HEADERS)


def http_get_content(url, allow_cache=False):
    md5 = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_file = _CACHE_DIR + md5
    html = ''
    if allow_cache and os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            html = f.read()
            print('from cache: ' + url)
    else:
        resp = _http_get(url)
        if resp.status_code != 200:
            print(url, 'STATUS:', resp.status_code)
        else:
            html = resp.content
            if allow_cache:
                with open(cache_file, 'wb') as f:
                    f.write(html)
                    print('from http: ' + url)
    return html


def url_to_bs(url):
    return BeautifulSoup(http_get_content(url), 'html.parser')


def parse_txt(lines, chapter_flag, skip_head=0, skip_tail=0):
    """将txt切割成不同章节, TODO: 适配更多类型, 需要样本"""
    if type(lines) == str:
        if lines.index('\r\n') >= 0:
            lines = lines.split('\r\n')
        else:
            lines = lines.split('\n')

    if skip_head > 0:
        lines = lines[skip_head:]

    if skip_tail > 0:
        lines = lines[:-skip_tail]

    chapters = []
    for line in lines:
        if len(line.strip()) == 0:
            continue
        if line.lstrip().startswith(chapter_flag):
            last_chapter = {'title': line, 'content': [f'<h3>{line}</h3>']}
            chapters.append(last_chapter)
        else:
            last_chapter['content'].append(line.replace('  ', '　'))

    for chapter in chapters:
        chapter['content'] = '<br>'.join(chapter['content'])

    return chapters
