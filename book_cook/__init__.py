
import argparse
import os
import sys

from .BookCook import BookCook


def _real_main(argv=None):
    parser = argparse.ArgumentParser(usage='%(prog)s [OPTIONS] URL [URL...]')
    parser.add_argument('url', metavar='URL', type=str)
    parser.add_argument('--cookie_file', dest='cookie_file', metavar='FILE', help='从浏览器的请求中复制 Header 中的 cookie')
    parser.add_argument('--store_path', dest='store_path', metavar='path', help='有些站点的某些内容希望永久存储, 用这个参数', )
    parser.add_argument('--chapter_re', dest='chapter_re', metavar='re', help='章节的正则匹配', )


    args = parser.parse_args()

    url = args.url
    if not url:
        print('cook-book: error: You must provide at least one URL.')
        sys.exit(1)

    if args.cookie_file is not None:
        if not os.path.exists(args.cookie_file):
            print('file not exists: %s' % args.cookie_file)
            sys.exit(1)
    if args.store_path is not None:
        if not os.path.exists(args.store_path):
            os.makedirs(args.store_path)

    bc_opts = {
        'cookie_file': args.cookie_file,
        'store_path': args.store_path,
        'chapter_re': args.chapter_re,
    }

    with BookCook(bc_opts) as bc:
        bc.cook(url)


def main(argv=None):
     _real_main(argv)
    # try:
    #     _real_main(argv)
    # except:
    #     sys.exit(1)
