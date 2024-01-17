from scrupy.crawler import CrawlHistory


def test_history_adds():
    """
    We test that adding a row, adds correctly to the history and that
    the stored values in the history are correct.
    """
    history = CrawlHistory()

    some_obj = type('obj', (), {'val': 1})
    history.add(some_obj, 2)
    history.add(3, 4)

    assert len(history) == 2
    assert history[0].id == 0
    assert history[0].request == some_obj
