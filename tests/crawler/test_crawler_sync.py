import time

import httpx
import pytest
from pytest_httpserver import HTTPServer

from scrupy import CrawlRequest
from scrupy.request import CrawlResponse


def test_crawler_basic(sync_crawler):
    """
       Test that:

        1. Crawler instantiates.
        2. Doesn't emit any error/exception in its most basic form.
        3. History is empty.
    """

    class MyCrawler(sync_crawler):
        pass

    crawler = MyCrawler()
    crawler.run()

    assert not crawler.history  # Empty


def test_crawler_crawls_start_urls(sync_crawler, httpserver):
    """
        Test that requests from the start_urls are crawled.
    """
    paths = [
        '/test1',
        '/test2'
    ]
    for path in paths:
        httpserver.expect_request(path)

    urls = [httpserver.url_for(path) for path in paths]

    crawler = sync_crawler(start_urls=urls, delay_per_request=0)

    crawler.run()

    assert len(crawler.history) == 2
    assert not isinstance(crawler.history[0].response.exception, httpx.ConnectError)


def test_crawler_crawls_mixed_urls(sync_crawler, httpserver):
    """
        Test that requests from the `start_urls` are crawled and `add_to_queue`.
    """
    paths = [
        '/test1',
        '/test2'
    ]
    for path in paths:
        httpserver.expect_request(path)

    httpserver.expect_request('/extra')

    urls = [httpserver.url_for(path) for path in paths]

    crawler = sync_crawler(start_urls=urls, delay_per_request=0)
    crawler.add_to_queue(httpserver.url_for('/extra'))

    crawler.run()

    assert len(crawler.history) == 3
    assert not isinstance(crawler.history[0].response.exception, httpx.ConnectError)


def test_crawler_correct_settings_on_before_crawl(sync_crawler, httpserver: HTTPServer, crawl_request):
    """
    Test that the correct settings end up in the actual final request.
    """
    user_agent = 'test_useragent'
    headers = {'testheader': 'one'}

    httpserver.expect_request('/test1')
    httpserver.expect_request('/test2')

    url1 = httpserver.url_for('/test1')
    url2 = httpserver.url_for('/test2')

    class crawler(sync_crawler):
        def on_before_crawl(self, request: CrawlRequest) -> CrawlRequest:
            if 'test1' in request.url.raw_url:
                request.headers = headers
                request.user_agent = user_agent
                return request
            return request

    c = crawler(
        start_urls=(url1, url2),
        delay_per_request=0
    )
    c.run()

    req1 = c.history[0].response.raw_response.request
    req2 = c.history[1].response.raw_response.request
    assert req1.headers.get('user-agent') == user_agent
    assert req2.headers.get('user-agent') == c.user_agent

    assert req1.headers.get('testheader', None) == 'one'
    assert req2.headers.get('testheader', None) is None


def test_crawler_uses_client(sync_crawler, httpserver: HTTPServer):
    """
        Attributes passed from the Crawler are also present in the final request when a client is being passed.
    """
    httpserver.expect_request('/test').respond_with_data('<html></html>')

    headers = {'my-header-key': 'my-header-value'}
    crawler_headers = {'other': 'one'}
    cookies = {'cookie-key': 'cookie-val'}

    client = httpx.Client(headers=headers, cookies=cookies)
    crawler = sync_crawler(client=client, delay_per_request=0, headers=crawler_headers)

    crawler.add_to_queue([httpserver.url_for("/test"), httpserver.url_for("/test")])
    crawler.run()

    # We test that the header makes it way to the final request, attrs injected through Client Scrupy's
    # CrawlRequests are unaware of it.

    assert all(
        map(lambda x: 'my-header-key' in x.response.raw_response.request.headers, crawler.history)
    )
    assert not all(map(lambda x: 'other' in x.response.raw_response.request.headers, crawler.history))
    assert all(map(lambda x: 'cookie-key' in x.response.raw_response.request.headers['cookie'],
                   crawler.history))
    assert len(crawler.history) == 2


def test_full_crawl(httpserver: HTTPServer, sync_crawler):
    """
    Test that a full basic crawl works.
    :return:
    """
    html = '<html></html>'
    httpserver.expect_request('/test').respond_with_data(html,
                                                         headers={'Content-Type': 'text/html'})

    crawler = sync_crawler(delay_per_request=0)
    crawler.add_to_queue(httpserver.url_for("/test"))
    crawler.run()
    response = crawler.history[0].response
    assert len(crawler.history) == 1
    with open('file.html', 'w') as f:
        f.write(response.html.text)
    assert response.is_html
    assert crawler.history[0].response.html.text == html


def test_crawler_run_forever(sync_crawler, crawl_request):
    """
    Test that crawler runs forever, but is properly stopped when `force_stop` is called.
    """

    class MyCrawler(sync_crawler):
        def on_crawled(self, response: CrawlResponse) -> None:
            self.force_stop()

    crawler = MyCrawler(delay_per_request=0, min_delay_per_tick=0)
    crawler.add_to_queue(['http://localhost:8080/', 'http://localhost:8080'])
    crawler.run(run_forever=True)
    assert len(crawler.history) == 1


def test_crawler_add_to_queue(sync_crawler, crawl_request):
    """
    Test that a crawler correctly adds to its queue.
    """
    crawler = sync_crawler()
    url = 'https://example.com'
    crawler.add_to_queue(['https://example.com', 'https://example.com/2'])
    assert len(crawler.frontier) == 2

    next = crawler.get_next()
    assert next.url == url

    crawler.add_to_queue([url, ], ignore_repeated=True)
    assert len(crawler.frontier) == 2


def test_crawler_keeps_crawling(sync_crawler, httpserver):
    """
    Test that the crawler keeps crawling after adding new urls to the queue.
    """

    httpserver.expect_request('/test')

    class TestCrawler(sync_crawler):
        max = 0

        def on_crawled(self, response: CrawlResponse) -> None:
            if self.max == 10:
                self.force_stop()

            self.add_to_queue(httpserver.url_for('/test'))
            self.max += 1

    crawler = TestCrawler(delay_per_request=0, start_urls=[httpserver.url_for('/test'), ])
    crawler.run()

    assert len(crawler.history) == 11


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
    # Fixme Parametrize this
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


def test_crawler_user_agent(crawler_base, crawl_request):
    default_user_agent = 'default_user_agent'
    c = crawler_base(
        randomize_user_agent_per_request=True,
        user_agent=default_user_agent
    )

    # # randomize_user_agent_per_request is True, test we get a chrome-like user-agent
    request = c._build_request(crawl_request)
    last_user_agent = request.user_agent
    assert '(KHTML, like Gecko) Chrome' in request.user_agent
    request = c._build_request('http://localhost')
    # Test that two randomly generated user-agents are not the same, this tests for 'randomness' so
    # technically both random generated user-agents could be the same and make this fail,
    # in that case, ignore and re-run this.
    assert request.user_agent != last_user_agent

    # randomize_user_agent_per_request is True, and the user has its custom generate_user_agent
    user_agent = 'someuseragent'
    c.generate_user_agent = lambda _: user_agent

    request = c._build_request('http://comein')
    assert request.user_agent == user_agent

    c.randomize_user_agent_per_request = False
    c.user_agent = default_user_agent
    request = c._build_request('http://otherurl')
    assert request.user_agent == default_user_agent
