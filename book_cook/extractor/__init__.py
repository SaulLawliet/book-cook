from .extractors import *

_ALL_CLASSES = [
    klass
    for name, klass in globals().items()
    if name.endswith('IE') and name != 'GenericIE'
]


def gen_extractor_classes():
    return _ALL_CLASSES


def get_info_extractor(ie_name):
    return globals()[ie_name + 'IE']
