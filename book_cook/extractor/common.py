
import re


class InfoExtractor(object):

    _downloader = None

    @classmethod
    def suitable(cls, url):
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        return cls._VALID_URL_RE.match(url) is not None

    @classmethod
    def ie_key(cls):
        return cls.__name__[:-2]

    def set_downloader(self, downloader):
        self._downloader = downloader

    def extract(self, url):
        ie_result = self._real_extract(url)
        return ie_result

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        pass
