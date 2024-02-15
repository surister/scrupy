import httpx
import pytest

from scrupy import CrawlRequest
from scrupy.crawler import Crawler
from scrupy.crawler.base import CrawlerBase


@pytest.mark.parametrize("crawler_settings, input_request, expected_request_settings", [
    ({"follow_redirects": True, 'timeout': 1}, 'http://localhost:8000', {"follow_redirects": True, 'timeout': 1}),
    ({"follow_redirects": False}, 'http://localhost:8000', {"follow_redirects": False}),
])
def test_crawler_crawl_request_build(crawler_settings, input_request, expected_request_settings):
    """
    Test that CrawlerBase._build_request returns a CrawlRequest object with the correct settings.
    """

    class Crawler(CrawlerBase):
        pass

    Crawler.__abstractmethods__ = set()

    request = Crawler(
        **crawler_settings,
    )._build_request(input_request)

    for k, v in crawler_settings.items():
        assert getattr(request, k) == expected_request_settings[k]


def test_s():
    client = httpx.Client(follow_redirects=False)
    c = Crawler(follow_redirects=True, client=client, user_agent='sexy')
    c.add_to_queue('http://localhost:8080')
    c.run()
