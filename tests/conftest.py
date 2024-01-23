import pytest

from scrupy import CrawlRequest, CrawlerBase


@pytest.fixture
def crawl_request():
    return CrawlRequest(
        url='https://www.myfixtureurl.com',
    )


@pytest.fixture
def crawler_base():
    class Crawler(CrawlerBase): pass
    Crawler.__abstractmethods__ = set()
    return Crawler
