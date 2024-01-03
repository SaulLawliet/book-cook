import re
from book_cook import utils
from book_cook.extractor.common import InfoExtractor


class TxtIE(InfoExtractor):
    _VALID_URL = r'file://.*.txt'

    def _real_extract(self, url):
        chapter_re = self._downloader.params.get('chapter_re')
        if not chapter_re:
            self._downloader.report_warning(
                '[TXT] 由于你没有指定章节的正则匹配(--chapter_re), 默认使用: "第.*章"')
            chapter_re = r'第.*章'

        name = url.split('/')[-1].split('.')[0]
        with open(url.replace('file://', '')) as f:
            volumes = utils.parse_txt(f.readlines(), chapter_re)

        return {
            'title': name,
            'author': name,
            'volumes': volumes
        }
