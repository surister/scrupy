import time

import pytest

from scrupy import CrawlerBase, CrawlRequest
from scrupy.request import CrawlResponse


def test_crawler_run_forever(crawler_base):
    """
    Test that crawler runs forever, but is properly stopped when `force_stop` is called.
    """

    class MyCrawler(crawler_base):
        def on_crawled(self, response: CrawlResponse) -> None:
            self.force_stop()

    crawler = MyCrawler(delay_per_request=0, min_delay_per_tick=0)
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


def test_crawler_add_to_queue(crawler_base):
    crawler = crawler_base()
    url = 'https://example.com'
    crawler.add_to_queue(url)

    assert len(crawler.urls) == 1
    assert crawler.urls[0] == url


def test_crawler_add_many_to_queue(crawler_base):
    crawler = crawler_base()
    url = 'http://example.com'
    urls = [url, 'http:example2.com']
    crawler.add_many_to_queue(urls)

    assert len(crawler.urls) == 2
    assert crawler.urls[0] == url

    crawler.history.add(CrawlRequest(url=url), response=None)
    crawler.add_many_to_queue([url, ], ignore_repeated=True)

    assert len(crawler.urls) == 2


def test_crawler_correct_settings(crawler_base):
    """
    Test that the right settings are assigned when building a crawl request.
    """

    user_agent = 'someuseragent'
    another_user_agent = 'anotheruseragent'
    crawler = crawler_base(user_agent=user_agent, follow_redirect=True)

    c1 = crawler._build_request(
        CrawlRequest(url='http://localhost',
                     user_agent=another_user_agent,
                     follow_redirect=False)
    )
    c2 = crawler._build_request('http://anotherurl.com')

    assert c1.user_agent == another_user_agent
    assert not c1.follow_redirect

    assert c2.user_agent == user_agent
    assert c2.follow_redirect


class UnexpectedTimingException(Exception):
    pass


def timed(condition: str = '>=', time_ms: int = 0):
    def deco(function):
        def wrapper(*args, **kwargs):
            now = time.time()
            r = function(*args, **kwargs)
            delta = (time.time() - now) * 1000
            if not eval(f'{delta} {condition} {time_ms}'):
                raise UnexpectedTimingException(
                    f'Expected execution time to be {condition}{time_ms} milliseconds but was: {delta} milliseconds')
            return r

        return wrapper

    return deco


@pytest.mark.timings
def test_crawler_correct_delays(crawler_base):
    @timed('<=', 1200)
    def t():
        crawler = crawler_base(min_delay_per_tick=0, delay_per_request=1000)
        crawler.add_to_queue('http://localhost:8000')
        crawler.run()

    t()

    @timed('<=', 1600)
    def t():
        crawler = crawler_base(min_delay_per_tick=1500, delay_per_request=1000)
        crawler.add_to_queue('http://localhost:8000')
        crawler.run()

    t()

    @timed('<=', 1600)
    def t():
        crawler = crawler_base(min_delay_per_tick=2000, delay_per_request=1000)
        crawler.add_to_queue('http://localhost:8000')
        crawler.run()

    with pytest.raises(UnexpectedTimingException):
        t()
