import httpx


def test_crawler_basic(async_crawler):
    """
       Test that:

        1. Crawler instantiates.
        2. Doesn't emit any error/exception in its most basic form.
        3. History is empty.
    """

    class MyCrawler(async_crawler):
        pass

    crawler = MyCrawler()
    crawler.run()

    assert not crawler.history  # Empty


def test_crawler_crawls_start_urls(async_crawler, httpserver):
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

    crawler = async_crawler(start_urls=urls)

    crawler.run()

    assert len(crawler.history) == 2
    assert not isinstance(crawler.history[0].response.exception, httpx.ConnectError)


def test_crawler_crawls_mixed_urls(async_crawler, httpserver):
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

    crawler = async_crawler(start_urls=urls)
    # TODO crawler.add_to_queue(httpserver.url_for('/extra'))
    # This cannot be tested since we cannot call async here, we should probably test this
    # with on_start_requests (which as of now doesn't exist, hence the t-odo)
    crawler.run()

    assert len(crawler.history) == 2
    assert not isinstance(crawler.history[0].response.exception, httpx.ConnectError)
