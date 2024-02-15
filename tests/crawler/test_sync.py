import time

import pytest

from scrupy import set_dev_mode
from scrupy.request import CrawlResponse, CrawlRequest


def test_crawler_run_forever(sync_crawler, crawl_request):
    """
    Test that crawler runs forever, but is properly stopped when `force_stop` is called.
    """

    class MyCrawler(sync_crawler):
        def on_crawled(self, response: CrawlResponse) -> None:
            self.force_stop()

    crawler = MyCrawler(delay_per_request=0, min_delay_per_tick=0)
    crawler.add_to_queue(['http://localhost:8080/', crawl_request])
    crawler.run(run_forever=True)
    assert len(crawler.history) == 1


def test_crawler_run_forever(sync_crawler, crawl_request):
    """
    Test that crawler stops running when it crawled everything.
    """

    class MyCrawler(sync_crawler):
        pass

    crawler = MyCrawler(delay_per_request=0, min_delay_per_tick=0)
    crawler.add_to_queue(['http://localhost:8080/', crawl_request])
    crawler.run(run_forever=False)
    assert len(crawler.history) == 2


def test_crawler_add_to_queue(sync_crawler, crawl_request):
    """
    Test that a crawler correctly adds to its queue.
    """
    crawler = sync_crawler()
    url = 'https://example.com'

    crawler.add_to_queue([url, crawl_request])
    assert len(crawler.frontier) == 2

    next = crawler.get_next()
    assert next.url == url

    crawler.add_to_queue([url, ], ignore_repeated=True)
    assert len(crawler.frontier) == 2


def test_crawler_correct_settings(sync_crawler):
    """
    Test that the right settings are assigned when building a crawl request.
    """

    user_agent = 'someuseragent'
    another_user_agent = 'anotheruseragent'
    crawler = sync_crawler(user_agent=user_agent, follow_redirect=True)

    c1 = crawler._build_request(
        CrawlRequest(url='http://localhost',
                     user_agent=another_user_agent,
                     follow_redirects=False)
    )
    c2 = crawler._build_request('http://anotherurl.com')

    assert c1.user_agent == another_user_agent
    assert not c1.follow_redirects

    assert c2.user_agent == user_agent
    assert c2.follow_redirects


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
