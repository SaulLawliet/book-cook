import hashlib
import logging
import os
import random
import re
import subprocess
import sys
import time
import colorlog
from fake_useragent import UserAgent

import requests
from bs4 import BeautifulSoup


_HEADERS = {
    "User-Agent": UserAgent(platforms="desktop").random,
}

# BookCook instance
BC = None

# 缓存命名空间, 由 extractor 定义
CACHE_NAMESPACE = None


def get_cache_path(filename):
    if not CACHE_NAMESPACE:
        raise ValueError("需设置 utils.CACHE_NAMESPACE 才能使用缓存")

    cache_dir = f"_cache/{CACHE_NAMESPACE}/"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir + filename


def _http_get(url, headers=_HEADERS):
    if BC.params["sleep_seconds"]:
        seconds = BC.params["sleep_seconds"]
        step = max(int(seconds * 0.3), 3)
        sleep = random.randint(seconds, seconds + step)
        logger.info(f"开启了请求限流, 本次暂停{sleep}s.")
        time.sleep(sleep)
    return requests.get(url, headers=_HEADERS | headers)


def http_get_content(url, allow_cache=False, headers=_HEADERS):
    return http_get_content_full_info(url, allow_cache, headers)[0]


def http_get_content_full_info(url, allow_cache=False, headers=_HEADERS):
    """return: body, md5, file_type"""

    file_type = None
    filename = url.split("?")[0].split("/")[-1]
    if "." in filename:
        file_type = filename.split(".")[-1]

    md5 = hashlib.md5(url.encode("utf-8")).hexdigest()
    cache_path = None
    if allow_cache:
        cache_path = get_cache_path(md5)
        if file_type is not None:
            cache_path += "." + file_type

    html = ""
    if cache_path and os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            html = f.read()
            logger.debug("from cache: " + url + " < " + cache_path)
    else:
        resp = _http_get(url, headers=headers)
        if resp.status_code != 200:
            logger.error(f"{url} STATUS: {resp.status_code} cache: {cache_path}")
        else:
            html = resp.content
            if cache_path:
                with open(cache_path, "wb") as f:
                    f.write(html)
                logger.debug("from http: " + url + " > " + cache_path)
            else:
                logger.debug("from http: " + url)
    return html, md5, file_type


def fetch_with_curl(url):
    result = subprocess.run(
        ["curl", "-s", url],
        capture_output=True,
    )

    if result.returncode == 0:
        logger.debug("from curl: " + url)
        return result.stdout

    else:
        logger.error(f"Error fetching {url}: {result.stderr}")
        raise Exception(f"Error: {result.stderr}")


def url_to_bs(url, allow_cache=False, headers=_HEADERS):
    return BeautifulSoup(
        http_get_content(url, allow_cache=allow_cache, headers=headers), "html.parser"
    )


def curl_to_bs(url):
    return BeautifulSoup(fetch_with_curl(url), "html.parser")


def str_to_bs(content):
    return BeautifulSoup(content, "html.parser")


def parse_txt(lines, chapter_flag, skip_head=0, skip_tail=0):
    """将txt切割成不同章节, TODO: 适配更多类型, 需要样本"""
    if isinstance(lines, str):
        lines = re.split("\r\n|\n", lines)
    if skip_head > 0:
        lines = lines[skip_head:]

    if skip_tail > 0:
        lines = lines[:-skip_tail]

    chapter_flag_re = re.compile(chapter_flag)
    chapters = []
    last_chapter = None
    for line in lines:
        if len(line.strip()) == 0:
            continue
        # ValueError: All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters
        # https://stackoverflow.com/a/25920392
        line = re.sub(
            "[^\u0020-\ud7ff\u0009\u000a\u000d\ue000-\ufffd\U00010000-\U0010ffff]+",
            "",
            line,
        )

        if chapter_flag_re.match(line.lstrip()):
            # 尝试跳过一些空章节
            if last_chapter and len(last_chapter["content"]) <= 1:
                chapters.pop()
            last_chapter = {"title": line, "content": [f"<h3>{line}</h3>"]}
            chapters.append(last_chapter)
        else:
            if last_chapter:
                last_chapter["content"].append(line.replace("  ", "　"))

    for chapter in chapters:
        chapter["content"] = "<br>".join(chapter["content"])

    return chapters


def read_file(path):
    with open(path) as f:
        return f.read()


def write_string(s, out=None):
    if out is None:
        out = sys.stderr
    out.write(s)
    out.flush()


def split_list(list, step):
    """将list变成等长的多个数组"""
    return [list[i : i + step] for i in range(0, len(list), step)]


def get_logger(name=None):
    # 用“/”的话方便在编辑器中定位到文件
    logger = logging.getLogger(name.replace(".", "/") if name else None)
    if not logger.handlers:
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s[%(levelname)s] %(name)-s:%(lineno)d: %(message)s",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger


logger = get_logger(__name__)
