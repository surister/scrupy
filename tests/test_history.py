import datetime
import json
import pathlib

from scrupy.crawler.history import CrawlHistory


def test_history_adds(crawl_request):
    """
    Test that adding a row, adds correctly to the history and that
    the stored values in the history are correct.
    """
    history = CrawlHistory()

    history.add(crawl_request, None, datetime.datetime.now())
    history.add(crawl_request, None, datetime.datetime.now())

    assert len(history) == 2
    assert history[0].id == 0
    assert history[1].id == 1
    assert history[0].request == crawl_request


def test_history_url_exists(crawl_request):
    """
    Test the function `CrawlHistory.exists`
    """
    url = crawl_request.url

    history = CrawlHistory()
    history.add(crawl_request, None, datetime.datetime.now())

    assert history.exists(url)
    assert not history.exists('http://urlthatdoesnotexist.com')


def test_history_persists(crawl_request, tmp_path):
    history = CrawlHistory()
    history.add(crawl_request, None, datetime.datetime(1, 1, 1, ))
    history.add(crawl_request, 'response', datetime.datetime(2, 2, 2))

    path = tmp_path / 'file.json'
    history.save(path)

    res = json.loads(pathlib.Path(path).read_text())
    expected = [
        {"id": 0,
         "request": {"url": "https://www.myfixtureurl.com", "method": "GET",
                     "headers": "unset", "user_agent": "unset",
                     "follow_redirects": "unset", "timeout": 5, "type": "httpx"},
         "response": None,
         "crawled_at": "0001-01-01 00:00:00"},
        {"id": 1,
         "request": {
             "url": "https://www.myfixtureurl.com", "method": "GET", "headers": "unset",
             "user_agent": "unset", "follow_redirects": "unset", "timeout": 5, "type": "httpx"},
         "response": "response",
         "crawled_at": "0002-02-02 00:00:00"}
    ]
    assert expected == res
