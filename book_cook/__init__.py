
import sys

from .BookCook import BookCook


def _parseOpts(argv):
    return sys.argv[1:]


def _real_main(argv=None):
    args = _parseOpts(argv)

    url = ''
    if len(args) > 0:
        url = args[0]

    if not url:
        print('cook-book: error: You must provide at least one URL.')
        sys.exit(1)

    bc_opts = {}
    with BookCook(bc_opts) as bc:
        bc.cook(url)


def main(argv=None):
    _real_main(argv)
    # try:
    #     _real_main(argv)
    # except:
    #     sys.exit(1)
