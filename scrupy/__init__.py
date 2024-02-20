import os
import logging

from .request import CrawlRequest
from .crawler.base import CrawlerBase

_dev_mode_key = 'SCRUPY_DEV_MODE'
DEV_MODE = os.getenv('_dev_mode_key', False)


def set_dev_mode(only_scrupy=False):
    muted_loggers = ['filelock', 'httpx', 'httpcore.http11', 'httpcore.connection']

    logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(name)s] %(message)s',
                        level=logging.DEBUG)

    if only_scrupy:
        for logger in muted_loggers:
            logging.getLogger(logger).setLevel(logging.INFO)


if DEV_MODE:
    set_dev_mode()

__all__ = [
    'CrawlRequest',
]
