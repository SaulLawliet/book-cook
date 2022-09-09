import json
import os
import sys

from ebooklib import epub

from book_cook import utils

from .extractor import gen_extractor_classes, get_info_extractor

_OUTPUT_DIR = '_output/'
if not os.path.exists(_OUTPUT_DIR):
    os.makedirs(_OUTPUT_DIR)


class BookCook(object):
    _ies = []
    _ies_instances = {}

    def __init__(self, params=None, auto_init=True):
        if auto_init:
            self.add_default_info_extractors()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def add_default_info_extractors(self):
        for ie in gen_extractor_classes():
            self.add_info_extractor(ie)

    def add_info_extractor(self, ie):
        if isinstance(ie, type):
            self._ies.append(ie)
        else:
            self._ies_instances[ie.ie_key()] = ie
            ie.set_downloader(self)

    def get_info_extractor(self, ie_key):
        ie = self._ies_instances.get(ie_key)
        if ie is None:
            ie = get_info_extractor(ie_key)()
            self.add_info_extractor(ie)
        return ie

    def cook(self, url):
        for ie in self._ies:
            if not ie.suitable(url):
                continue
            ie = self.get_info_extractor(ie.ie_key())
            return self._cook(url, ie)
        else:
            print('no suitable InfoExtractor for URL %s' % url)
            sys.exit(1)

    def _epub_create_html(self, title, file_name, content):
        rtn = epub.EpubHtml(title=title, file_name=file_name, content=content)
        self.book.add_item(rtn)
        self.book.spine.append(rtn)
        return rtn

    def _cook(self, url, ie):
        ie_result = ie.extract(url)
        if ie_result is None:
            return

        self.book = epub.EpubBook()

        self.book.set_identifier(ie_result['identifier'])
        self.book.set_title(ie_result['title'])
        self.book.set_language(ie_result['language'])
        self.book.add_author(ie_result['author'])

        if 'cover' in ie_result:
            cover_name = 'cover.' + ie_result['cover'].split('.')[-1]
            self.book.set_cover(cover_name, utils.http_get_content(ie_result['cover'], allow_cache=True))

        self.book.spine.append('nav')
        for i, volume in enumerate(ie_result['volumes']):
            # volume
            v = self._epub_create_html(
                volume['title'], f'v{i}.xhtml', f'<h2>{volume["title"]}</h2>')
            self.book.toc.append([v, []])
            # chapters
            for j, chapter in enumerate(volume['chapters']):
                c = self._epub_create_html(
                    chapter['title'], f'v{i}c{j}.xhtml', chapter['content'])
                self.book.toc[-1][1].append(c)

        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        del ie_result['volumes']
        print(json.dumps(ie_result, indent=2, ensure_ascii=False))

        output_name = f'{_OUTPUT_DIR}{ie_result["file_name"]}.epub'
        epub.write_epub(output_name, self.book, {})
        print('<SUCCESS>', output_name)
