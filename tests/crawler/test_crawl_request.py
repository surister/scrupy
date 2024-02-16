from scrupy.request import CrawlRequest
import pytest


def test_crawl_request_valid_url():
    """
    Test CrawlRequest raises an exception when not bad url is given.
    :return:
    """
    with pytest.raises(ValueError):
        CrawlRequest(url='string')


def test_crawl_request_valid_url_parts():
    """
    Test a CrawlRequest's Url is properly formed.
    :return:
    """
    url = 'https://domain.com'
    c = CrawlRequest(url=url)

    assert c.url.netloc
    assert c.url == url
    assert str(c.url) == url
    assert c.url.domain == 'domain'
