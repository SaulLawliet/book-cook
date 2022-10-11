import datetime
from fileinput import filename
import json
import os
from pydoc import cli
import random
import time
import requests
from ... import utils
from ..common import InfoExtractor


class GeekbangIE(InfoExtractor):
    """
    TODO: 代码没有格式化
    TODO: 没有解析 LaTeX
    """
    _VALID_URL = r'https://time.geekbang.org/column/\d+'

    def _real_extract(self, url):
        product_id = url.split('/')[-1]

        cookie_file = self._downloader.params.get('cookie_file')
        if cookie_file is None:
            self._downloader.report_error('[极客时间] 需要指定 <COOKIE>')
            return None

        store_path = self._downloader.params.get('store_path')
        if store_path is None:
            self._downloader.report_warning('[极客时间] 专栏文章的存储目录需要指定\n\t好处1: 接口容易限频, 方便重试\n\t好处2: 会员过期后也有备份')
            return None

        client = GeekbangClient(self._downloader, utils.read_file(cookie_file).strip(), store_path)

        auth = client.auth()
        if auth['code'] != 0:
            self._downloader.report_error(auth['error'])
            return None
        self._downloader.to_stdout(f"当前用户: {auth['data']['nick']}\n")

        info = client.info(product_id)
        title = info['data']['share']['title'].replace(' ', '')
        cid = info['data']['extra']['cid']
        self._downloader.to_stdout(f'获取专栏成功: {title}\n')

        volumes = []
        volumes_hash = {}
        chapter_ids = []

        chapters = client.chapters(product_id, cid)
        for chapter in chapters['data']:
            chapter_ids.append(chapter['id'])
            volume = {
                'title': '%s (%d讲)' % (chapter['title'], chapter['article_count']),
                'chapters': []
            }
            volumes.append(volume)
            volumes_hash[chapter['id']] = volume

        self._downloader.to_stdout(f"构建章节成功: {list(map(lambda x: x['title'], volumes))}\n")

        articles = client.articles(product_id, chapter_ids)
        store_dir = '%s-%s' % (product_id, info['data']['title'])

        for article in articles['data']['list']:
            article = client.article_with_store(store_dir, article['id'], article['article_title'])

            volumes_hash[article['data']['chapter_id']]['chapters'].append({
                'title': article['data']['article_title'],
                'content': f"<h1>{article['data']['article_title']}</h1><h3>{datetime.datetime.fromtimestamp(article['data']['article_ctime'])}</h3>{article['data']['article_content']}"
            })

        return {
            'identifier': title,
            'title': title,
            'language': 'zh-cn',
            'author': info['data']['author']['name'],
            'cover': info['data']['cover']['rectangle'],
            'file_name': title,
            'volumes': volumes
        }


class GeekbangClient:

    def __init__(self, downloader, cookie, store_path) -> None:
        self._downloader = downloader
        self.headers = {
            'Cookie': cookie,
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
        }
        self.store_path = store_path


    def auth(self):
        headers = {'Referer': 'https://time.geekbang.org/'}
        headers.update(self.headers)

        return requests.get(
            f'https://account.geekbang.org/serv/v1/user/auth?t={int(time.time() * 1000)}', headers=headers).json()

    def info(self, product_id):
        headers = {'Referer': f'https://time.geekbang.org/column/intro/{product_id}'}
        headers.update(self.headers)

        json = {
            'product_id': int(product_id),
            'with_recommend_article': True
        }

        return requests.post('https://time.geekbang.org/serv/v3/column/info', json=json, headers=headers).json()

    def chapters(self, product_id, cid):
        headers = {'Referer': f'https://time.geekbang.org/column/intro/{product_id}'}
        headers.update(self.headers)

        json = {
            'cid': int(cid)
        }

        return requests.post('https://time.geekbang.org/serv/v1/chapters', json=json, headers=headers).json()

    def articles(self, product_id, chapter_ids):
        headers = {'Referer': f'https://time.geekbang.org/column/intro/{product_id}'}
        headers.update(self.headers)

        json = {
            'cid': int(product_id),
            'size': 500,
            'prev': 0,
            'order': 'earliest',
            'sample': False,
            'chapter_ids': chapter_ids
        }

        return requests.post('https://time.geekbang.org/serv/v1/column/articles',
                             json=json,
                             headers=headers).json()

    def article(self, article_id):
        headers = {'Referer': f'https://time.geekbang.org/column/article/{article_id}'}
        headers.update(self.headers)

        json = {
            'id': article_id,
            'include_neighbors': True,
            'is_freelyread': True
        }

        return requests.post('https://time.geekbang.org/serv/v1/article',
                             json=json,
                             headers=headers).json()

    def article_with_store(self, store_dir, article_id, title):
        dir = '%s/%s' % (self.store_path, store_dir)
        if not os.path.exists(dir):
            os.makedirs(dir)

        filename = '%s/%s/%s.json' % (self.store_path, store_dir, article_id)
        if os.path.exists(filename):
            with open(filename) as f:
                self._downloader.to_stdout(f'读取缓存成功: {title}')
                return json.load(f)

        data = self.article(article_id)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self._downloader.to_stdout(f"保存文章成功: {title}")
        time.sleep(random.randint(5, 10))
        return data
