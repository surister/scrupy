import httpx
from pytest_httpserver import HTTPServer

from scrupy import CrawlRequest
from scrupy.crawler import Crawler


def test_crawler_basic(sync_crawler):
    """
        We test that:

        1. Crawler instantiates
        2. Doesn't emit any error/exception in its most basic form
        3. History is empty of any stuff
        :return:
    """

    class MyCrawler(sync_crawler):
        pass

    crawler = MyCrawler()
    crawler.run()

    assert not crawler.history  # Empty


def test_crawler_crawls(sync_crawler):
    """
        Test that requests from the original url are crawled.
    """
    urls = [
        CrawlRequest('http://localhost:12345678'),
        'http://localhost:87654321'
    ]

    crawler = sync_crawler(start_urls=urls, delay_per_request=0)
    crawler.run()

    assert len(crawler.history) == 2
    # Fails since nothing should be on port http://localhost:12345678
    assert isinstance(crawler.history[0].response.exception, httpx.ConnectError)


def test_crawler_uses_client(httpserver: HTTPServer, sync_crawler):
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

    print(crawler.history[0].response.raw_response.cookies)
    assert all(map(lambda x: 'my-header-key' in x.response.raw_response.request.headers, crawler.history))
    assert all(map(lambda x: 'other' in x.response.raw_response.request.headers, crawler.history))
    assert all(map(lambda x: 'cookie-key' in x.response.raw_response.request.headers['cookie'], crawler.history))
    assert len(crawler.history) == 2


def test_full_crawl(httpserver: HTTPServer, sync_crawler):
    """
    Test that a full basic crawl works.
    :return:
    """
    html = '<html></html>'
    httpserver.expect_request('/test').respond_with_data(html, headers={'Content-Type': 'text/html'})

    crawler = sync_crawler(delay_per_request=0)
    crawler.add_to_queue(httpserver.url_for("/test"))
    crawler.run()
    response = crawler.history[0].response
    assert len(crawler.history) == 1
    with open('file.html', 'w') as f:
        f.write(response.html.text)
    assert response.is_html
    assert crawler.history[0].response.html.text == html


