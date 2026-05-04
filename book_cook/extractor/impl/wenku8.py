from urllib.parse import urljoin
from ... import utils
from ..common import InfoExtractor

logger = utils.get_logger(__name__)


class WenKu8IE(InfoExtractor):
    _VALID_URL = r"https://www.wenku8.net/book/\d+.htm"

    def _real_extract(self, url):
        # !!! 该站点升级了反爬机制，改用curl请求
        bs = utils.curl_to_bs(url)

        id = url.split("/")[-1].split(".")[0]

        utils.CACHE_NAMESPACE = f"{self.ie_key()}/{id}"

        # ['Re:从零开始的异世界生活 ', ' 长月达平 ', ' MF文库J ', ' 轻小说文库']
        info = bs.title.text.split("-")

        logger.info(info)

        toc_url = bs.select_one("span:nth-child(1) div a").get("href")
        toc_bs = utils.curl_to_bs(urljoin(url, toc_url))

        volumes = []
        volume_name = None
        for tr in toc_bs.select("tr"):
            if volume_name is None:
                v = tr.select_one(".vcss")
                if v:
                    volume_name = v.text
            else:
                # 下载地址: https://dl1.wenku8.com/packtxt.php?aid=2943&vid=118807&charset=utf-8
                # 2943: 书的ID, 118807: 第一章的ID减1
                volume_id = int(tr.select_one(".ccss a").get("href").split(".")[0]) - 1
                volume_url = (
                    "https://dl1.wenku8.com/packtxt.php?aid=%s&vid=%d&charset=utf-8"
                    % (id, volume_id)
                )
                volume_body = str(
                    utils.http_get_content(volume_url, allow_cache=True),
                    "utf-16",
                )

                volumes.append(
                    {
                        "title": volume_name,
                        "chapters": utils.parse_txt(
                            volume_body, volume_name, skip_head=1, skip_tail=2
                        ),
                    }
                )
                volume_name = None
        file_name = info[0].strip().replace(":", "")
        status = bs.select_one("#content > div > table tr+ tr td:nth-child(3)")
        if status and status.text == "文章状态：连载中":
            file_name += "_连载至_" + volumes[-1]["title"]

        return {
            "title": info[0].strip(),
            "author": info[1].strip(),
            "cover": bs.select_one("div+ table img").get("src"),
            "file_name": file_name,
            "volumes": volumes,
        }
