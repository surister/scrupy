from scrupy.crawler import CrawlHistory


def test_history_adds():
    """
    Test that adding a row, adds correctly to the history and that
    the stored values in the history are correct.
    """
    history = CrawlHistory()

    some_obj = type('obj', (), {'val': 1})
    history.add(some_obj, 2)
    history.add(3, 4)

    assert len(history) == 2
    assert history[0].id == 0
    assert history[0].request == some_obj


def test_history_url_exists(crawl_request):
    """
    Test the function `CrawlHistory.exists`
    """
    url = crawl_request.url
    history = CrawlHistory()
    history.add(crawl_request, None)

    assert history.exists(url)
    assert not history.exists('http://urlthatdoesnotexist.com')
