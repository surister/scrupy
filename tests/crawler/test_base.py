import pytest

from scrupy import CrawlerBase, CrawlRequest
from scrupy.request import CrawlResponse


def test_crawler_run_forever():
    """
    Test that crawler runs forever, but is properly stopped when `force_stop` is called.
    """
    class MyCrawler(CrawlerBase):
        def on_crawled(self, response: CrawlResponse) -> None:
            self.force_stop()

    # This allows us to instantiate an ABC without implementing all abc.abstractmethods
    MyCrawler.__abstractmethods__ = set()

    crawler = MyCrawler()
    crawler.add_to_queue('http://localhost:8080/')
    crawler.run(run_forever=True)

    assert len(crawler.history) == 1


@pytest.mark.parametrize("input_request", [
    'http://localhost:8000',
    CrawlRequest('http://localhost:8000')
])
def test_crawler_crawl_request_build(input_request):
    """
    Test that CrawlerBase._build_request returns a CrawlRequest object with the correct Url.
    """

    c = type('c', (CrawlerBase,), {})

    # This allows us to instantiate an ABC without implementing all abc.abstractmethods
    c.__abstractmethods__ = set()

    request = c()._build_request(input_request)
    assert isinstance(request, CrawlRequest)
    assert request.url == 'http://localhost:8000'


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
