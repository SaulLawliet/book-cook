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

    _id_hash = {}  # 防止加入重复的资源

    def __init__(self, params=None, auto_init=True):
        utils.BC = self

        self.params = params

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


    def to_stdout(self, message):
        output = message + '\n'
        utils.write_string(output, sys.stdout)

    def to_stderr(self, message):
        output = message + '\n'
        utils.write_string(output, sys.stderr)

    def report_warning(self, message):
        warning_message = '%s %s' % ('\033[0;33mWARNING:\033[0m', message)
        self.to_stderr(warning_message)

    def report_error(self, message):
        error_message = '%s %s' % ('\033[0;31mERROR:\033[0m', message)
        self.to_stderr(error_message)

    def cook(self, url):
        for ie in self._ies:
            if not ie.suitable(url):
                continue
            ie = self.get_info_extractor(ie.ie_key())
            utils.IE = ie
            return self._cook(url, ie)
        else:
            self.report_error('no suitable InfoExtractor for URL %s' % url)
            sys.exit(1)

    def _process_content(self, content):
        """处理图片链接"""
        bs = utils.str_to_bs(content)
        for img in bs.select('img'):
            body, id, file_type = utils.http_get_content_full_info(img['src'], allow_cache=True)

            if id not in self._id_hash:
                self._id_hash[id] = None
                # 这里处理的比较简单: 如果不是png, 就是jpeg
                media_type = 'image/png'
                if file_type != 'png':
                    media_type = 'image/jpeg'

                self.book.add_item(epub.EpubImage(
                    uid=id,
                    file_name=id,
                    media_type=media_type,
                    content=body
                ))

            img['src'] = id
        return str(bs)

    def _epub_create_html(self, title, file_name, content):
        rtn = epub.EpubHtml(title=title, file_name=file_name, content=self._process_content(content))
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
            if 'chapters' in volume:
                # volume
                v = self._epub_create_html(
                    volume['title'], f'v{i}.xhtml', f'<h2>{volume["title"]}</h2>')
                self.book.toc.append([v, []])
                # chapters
                for j, chapter in enumerate(volume['chapters']):
                    c = self._epub_create_html(
                        chapter['title'], f'v{i}c{j}.xhtml', chapter['content'])
                    self.book.toc[-1][1].append(c)
            else:
                self.book.toc.append(self._epub_create_html(volume['title'], f'v{i}.xhtml', volume['content']))

        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        del ie_result['volumes']
        self.to_stdout(json.dumps(ie_result, indent=2, ensure_ascii=False))

        output_name = f'{_OUTPUT_DIR}{ie_result["file_name"]}.epub'
        epub.write_epub(output_name, self.book, {})
        self.to_stdout('<SUCCESS> %s' % output_name)
