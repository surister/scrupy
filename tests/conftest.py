import pytest

from scrupy import CrawlRequest
from scrupy.crawler.crawler import Crawler, AsyncCrawler

from scrupy.request import CrawlResponse


@pytest.fixture
def crawl_request():
    return CrawlRequest(
        url='https://www.myfixtureurl.com',
    )


@pytest.fixture
def sync_crawler():
    return Crawler


@pytest.fixture
def async_crawler():
    return AsyncCrawler


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
