import pkgutil
import importlib
from pathlib import Path

from book_cook.extractor.common import InfoExtractor


_ALL_CLASSES = {}


def get_info_extractor(ie_name):
    return gen_extractor_classes()[ie_name]


def gen_extractor_classes():
    if len(_ALL_CLASSES) > 0:
        return _ALL_CLASSES

    impl_path = str(Path(__file__).parent / "impl")

    for _, module_name, _ in pkgutil.iter_modules([impl_path]):
        module = importlib.import_module(f".impl.{module_name}", package=__package__)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if (
                isinstance(attr, type)
                and issubclass(attr, InfoExtractor)
                and attr is not InfoExtractor
            ):
                _ALL_CLASSES[attr.ie_key()] = attr

    return _ALL_CLASSES
