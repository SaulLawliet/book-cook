import re
from ... import utils
from ..common import InfoExtractor

logger = utils.get_logger(__name__)


class Po18IE(InfoExtractor):
    _VALID_URL = r"https://www.po18.tw/books/\d+"

    def _real_extract(self, url):
        URL_PREFIX = "https://www.po18.tw/books/"
        book_id = url.split("/")[4]

        utils.CACHE_NAMESPACE = f"{self.ie_key()}/{book_id}"

        cookie_file = self._downloader.params.get("cookie_file")
        if cookie_file is None:
            logger.error("[PO18] 需要指定 <COOKIE>")
            return None

        headers = {"Cookie": utils.read_file(cookie_file).strip()}

        info = utils.url_to_bs(URL_PREFIX + book_id, headers=headers)
        book_name = info.select_one(".book_name").text
        book_author = info.select_one(".book_author").text

        logger.info([book_name, book_author])

        volumes = []

        page_num = 1
        while True:
            logger.info(f"fetching page {page_num} ...")
            articles = utils.url_to_bs(
                URL_PREFIX + book_id + f"/articles?page={page_num}", headers=headers
            )

            for c in articles.select(".c_l"):
                chaptname = c.select_one(".l_chaptname").text
                chapter = {"title": chaptname, "content": None}
                volumes.append(chapter)

                date = c.select_one(".l_date").text
                font = c.select_one(".l_font").text
                header = f"<p>{date} | {font}<p>"
                a = c.select_one("a")
                if a.get("href").startswith("javascript:"):
                    chapter["content"] = (
                        f"{header}<h1>{chaptname}</h1><p>需付费：<b>{a.text}</b>"
                    )
                else:
                    article_url = "https://www.po18.tw" + a.get("href")
                    content_header = {"Referer": article_url}
                    content_header.update(headers)

                    content = utils.http_get_content(
                        article_url.replace("articles", "articlescontent"),
                        True,
                        content_header,
                    ).decode("utf-8")
                    # 这里要追加一个 '</p>', 原文不是标准的 HTML
                    lines = list(
                        map(
                            lambda x: re.sub("^.*</blockquote>", "", x) + "</p>",
                            content.split("\r"),
                        )
                    )
                    chapter["content"] = f"{header}{''.join(lines)}"

            has_next_page = False
            for page_a in articles.select(".page a"):
                if page_a.text == ">":
                    has_next_page = True

            if has_next_page:
                page_num += 1
            else:
                break

        return {
            "title": book_name,
            "author": book_author,
            "cover": info.select_one(".book_cover img").get("src"),
            "volumes": volumes,
        }
