
import re
from bs4 import BeautifulSoup
import requests
from ... import utils
from ..common import InfoExtractor


class Po18IE(InfoExtractor):
    _VALID_URL = r'https://www.po18.tw/books/\d+'

    def _real_extract(self, url):
        URL_PREFIX = 'https://www.po18.tw/books/'
        book_id = url.split('/')[4]

        cookie_file = self._downloader.params.get('cookie_file')
        if cookie_file is None:
            self._downloader.report_error('[PO18] 需要指定 <COOKIE>')
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Cookie': utils.read_file(cookie_file).strip()
        }

        info = utils.url_to_bs(URL_PREFIX + book_id, headers=headers)
        book_name = info.select_one('.book_name').text
        book_author = info.select_one('.book_author').text

        articles = utils.url_to_bs(
            URL_PREFIX + book_id + '/articles', headers=headers)

        volumes = []

        for c in articles.select('.c_l'):
            chaptname = c.select_one('.l_chaptname').text
            chapter = {
                'title': chaptname,
                'content': None
            }
            volumes.append(chapter)

            date = c.select_one('.l_date').text
            font = c.select_one('.l_font').text
            header = f'<p>{date} | {font}<p>'
            a = c.select_one('a')
            if a.get('href').startswith('javascript:'):
                chapter['content'] = f'{header}<h1>{chaptname}</h1><p>需付费：<b>{a.text}</b>'
            else:
                article_url = 'https://www.po18.tw' + a.get('href')
                content_header = {
                    'Referer': article_url
                }
                content_header.update(headers)

                content = utils.http_get_content(article_url.replace(
                    'articles', 'articlescontent'), True, content_header).decode("utf-8")
                # 这里要追加一个 '</p>', 原文不是标准的 HTML
                lines = list(map(lambda x: re.sub(
                    u'^.*</blockquote>', '', x) + '</p>', content.split('\r')))
                chapter['content'] = f'{header}{"".join(lines)}'

        return {
            'title': book_name,
            'author': book_author,
            'cover': info.select_one('.book_cover img').get('src'),
            'volumes': volumes
        }
