from book_cook import utils
from book_cook.extractor.common import InfoExtractor


class a06akIE(InfoExtractor):
    _VALID_URL = r'https://www.06ak.com/book/\d+'

    def _real_extract(self, url):
        URL_PREFIX = 'https://www.06ak.com'
        book = utils.url_to_bs(url)
        volumes = []
        for a in book.select('#ul_all_chapters li a'):
            articles = [f'<h2>{a.text}</h2>']
            link = URL_PREFIX + a.get('href')
            while link:
                catalog = utils.url_to_bs(link, allow_cache=True)
                articles.append(str(catalog.select_one('#article')))
                next = catalog.select_one('#next_url')
                if next.text.strip() == '下一页':
                    link = URL_PREFIX + next.get('href')
                else:
                    link = None
            volumes.append({'title': a.text, 'content': ''.join(articles)})

        title = book.select_one('.novel_info_title h1').text.strip()
        author = book.select_one('.novel_info_title i a').text.strip()
        title_author = f'{title} - {author}'

        return {
            'language': 'zh-cn',
            'identifier': title_author,
            'title': title_author,
            'file_name': title,
            'author': author,
            'cover': book.select_one('.novel_info_main img').get('src'),
            'volumes': volumes
        }
