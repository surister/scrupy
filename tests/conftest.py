import pytest

from scrupy import CrawlRequest, CrawlerBase
from scrupy.request import CrawlResponse


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


@pytest.fixture
def successful_response(crawl_request):
    return CrawlResponse(
        request=crawl_request,
        raw_response=object,
        exception=None,
        method='GET',
        status_code=200,
        http_version='HTTP/1.1',
        headers={}
    )
