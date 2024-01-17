import httpx

from scrupy import CrawlRequest
from scrupy.crawler import HttpxCrawler


def test_crawler_basic():
    """
    We test that:

    1. Crawler instantiates
    2. Doesn't emit any error/exception in its most basic form
    3. History is empty of any stuff
    :return:
    """

    class MyCrawler(HttpxCrawler):
        pass

    crawler = MyCrawler()
    crawler.crawl()

    assert not crawler.history  # Empty


def test_crawler_crawls():
    """
    Test that requests from the original url are crawled.
    """
    class MyCrawler(HttpxCrawler):
        urls = [
            CrawlRequest('http://localhost:12345678')
            # TODO Also add a 'str' url, our system should manage that
        ]

    crawler = MyCrawler()
    crawler.crawl()

    assert len(crawler.history) == 1
    # Fails since nothing should be on port http://localhost:12345678
    assert isinstance(crawler.history[0].response.exception, httpx.ConnectError)
