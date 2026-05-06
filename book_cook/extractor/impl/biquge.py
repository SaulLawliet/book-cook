from book_cook import utils
from book_cook.extractor.common import InfoExtractor

logger = utils.get_logger(__name__)


class BiqugeIE(InfoExtractor):
    _VALID_URL = r"https://(m.|)biquge.tw/book/\d+.html"

    def _real_extract(self, url):
        if "m.biquge.tw" in url:
            logger.info("当前是【繁体】，域名去掉“m.”可以切换成【简体】")
        else:
            logger.info("当前是【简体】，域名加上“m.”可以切换成【繁体】")

        book_id = url.split("/")[-1].split(".")[0]

        utils.CACHE_NAMESPACE = f"{self.ie_key()}/{book_id}"

        # 测试阶段，全部用缓存
        page_home = utils.url_to_bs(url)

        book_name = page_home.select_one(".book h1").text.strip()
        book_author = page_home.select_one(".book h2 a").text.strip()
        book_cover = page_home.select_one(".book .cover img").get("src")
        logger.info([book_name, book_author, book_cover])

        host = url.split("/book/")[0]

        # 目录：https://biquge.tw/book/8041169/
        page_catalog = utils.url_to_bs(f"{host}/book/{book_id}/")

        chapters = []
        for li in page_catalog.select(".booklist li"):
            dom_a = li.select_one("a")
            chapter_name = dom_a.text.strip()
            chapter_url = dom_a.get("href")
            page_content = utils.url_to_bs(host + chapter_url, allow_cache=True)

            content_title = page_content.select_one("h1").text.strip()
            # 未找到示例，先加个判断，后续如果有翻页的示例再修改代码
            if not content_title.endswith("（1 / 1）"):
                logger.error(f"章节有翻页，需要修改代码: {content_title}")
                exit(1)

            content = page_content.select_one("#chaptercontent")
            chapters.append(
                {"title": chapter_name, "content": f"<h3>{chapter_name}</h3>{content}"}
            )

        return {
            "title": book_name,
            "author": book_author,
            "cover": book_cover,
            "volumes": chapters,
        }
