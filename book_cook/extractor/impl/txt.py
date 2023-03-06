import re
from book_cook import utils
from book_cook.extractor.common import InfoExtractor


class TxtIE(InfoExtractor):
    _VALID_URL = r'file://.*.txt'

    def _real_extract(self, url):
        chapter_re = self._downloader.params.get('chapter_re')
        if not chapter_re:
            self._downloader.report_warning('[TXT] 由于你没有指定章节的正则匹配(--chapter_re), 默认使用: "第.*章"')
            chapter_re = r'第.*章'

        name = url.split('/')[-1].split('.')[0]
        volumes = []
        with open(url.replace('file://', '')) as f:
            all_chapters = utils.parse_txt(f.readlines(), chapter_re)
            # 直接每10个合并成一个
            step = 10
            for chapters in [all_chapters[i:i+step] for i in range(0, len(all_chapters), step)]:
                volumes.append({
                    'title': re.findall(chapter_re, chapters[0]['title'])[0] + ' - ' + re.findall(chapter_re, chapters[-1]['title'])[0],
                    'chapters': chapters
                })

        return {
            'language': 'zh-cn',
            'identifier': name,
            'title': name,
            'file_name': name,
            'author': name,
            'volumes': volumes
        }
