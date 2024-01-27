from scrupy.request import CrawlRequest
import pytest


def test_crawl_request_valid_url():
    with pytest.raises(Exception):
        CrawlRequest(url='abc')


def test_crawl_request_valid_url_parts():
    url = 'https://domain.com'
    c = CrawlRequest(url=url)

    assert c.url.netloc
    assert c.url == url
    assert str(c.url) == url