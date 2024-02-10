import pytest

from scrupy import CrawlRequest
from scrupy.crawler.base import CrawlerBase


@pytest.mark.parametrize("crawler_settings, input_request, expected_request_settings", [
    ({"follow_redirect": True, }, 'http://localhost:8000', {"follow_redirect": True}),

    ({"follow_redirect": True, }, CrawlRequest('http://localhost:8000', follow_redirect=False),
     {"follow_redirect": False}),

    ({"follow_redirect": False, }, CrawlRequest('http://localhost:8000', follow_redirect=True),
     {"follow_redirect": True}),

])
def test_crawler_crawl_request_build(crawler_settings, input_request, expected_request_settings):
    """
    Test that CrawlerBase._build_request returns a CrawlRequest object with the correct Url.
    """

    class Crawler(CrawlerBase):
        pass

    Crawler.__abstractmethods__ = set()

    request = Crawler(
        **crawler_settings,
    )._build_request(input_request)

    for k, v in crawler_settings.items():
        assert getattr(request, k) == expected_request_settings[k]
