import collections
import time
from collections import deque
from typing import Optional

import httpx

from .request import CrawlRequest, CrawlResponse, UNSET


class CrawlHistory:
    def __init__(self):
        self.history = []
        self.i = 0

    def add(self, request: CrawlRequest, response: CrawlResponse):
        self.history.append(
            collections.namedtuple('history_row', ['id', 'request', 'response'])
                (
                **{
                    'id': self.i,
                    'request': request,
                    'response': response,
                }
            )
        )

        self.i += 1

    def __getitem__(self, item):
        return self.history[item]

    def __iter__(self):
        return iter(self.history)

    def __str__(self):
        return str(self.history)

    def __len__(self):
        return len(self.history)

    def __repr__(self):
        return self.__str__()


class Crawler:
    method: str = 'GET'
    urls: deque[CrawlRequest] = deque()
    history = CrawlHistory()

    def __init__(self,
                 *,
                 delay_s: int = None,
                 follow_redirect: Optional[bool] = None,
                 use_default_client: bool = False,
                 client=None,
                 ):
        self.delay_s = delay_s
        self.use_default_client = use_default_client
        self.follow_redirect = follow_redirect

        if client and not isinstance(client, getattr(self.__class__, 'client_type')):
            raise AttributeError('Wrong client type')  # Improve exception

        if client and use_default_client:
            raise Exception('Cannot have client=True and use_default_client = True')

        self.client = client

        if not self.client and self.use_default_client:
            self.client = self.get_default_client()

    def add_many_to_queue(self, urls: list[CrawlRequest | str], add_left: bool = False):
        """
        Adds several elements to the crawling queue.

        Add a list of CrawlRequest
            >>> requests = [
            >>> CrawlRequest(url='https://www.google.com', method=POST),
            >>> CrawlRequest(url='https://www.reddit.com', method=GET),
            >>> CrawlRequest(url='https://www.google.co.uk', method=POST)
            >>> ]
            >>> Crawler.add_to_queue(requests)



            Add a list of urls
            >>> Crawler.add_to_queue(
            >>> ['https://www.google.com', 'https://www.reddit.com', 'https://www.linkedin.com']
            >>> )

        :param urls:
        :param add_left:
        :return:
        """
        if isinstance(urls[0], str):
            urls = [CrawlRequest(url=url) if isinstance(url, str) else url for url in urls]

        self.urls.extendleft(urls) if add_left else self.urls.extend(urls)

    def add_to_queue(self, url: CrawlRequest | str, add_left: bool = False) -> None:
        """
        Adds a new CrawlRequest to the queue.

        Examples:

            Add one new CrawlRequest
            >>> new_request = CrawlRequest(url='https://www.google.com', method=POST)
            >>> Crawler.add_to_queue(new_request)

            Add one new url
            >>> Crawler.add_to_queue('https://www.google.com')
        """

        if isinstance(url, str):
            url = CrawlRequest(url)
        self.urls.appendleft(url) if add_left else self.urls.append(url)

    def get_from_queue(self):
        return self.urls.pop()

    def on_crawled(self, response: CrawlResponse) -> None:
        pass

    def get_default_client(self) -> object:
        pass

    def crawl(self) -> None:
        while self.urls:
            request = self.get_from_queue()

            if self.follow_redirect is not None and request.follow_redirect is UNSET:
                # Priority is: CrawlRequest passed settings > Crawler settings
                request.follow_redirect = self.follow_redirect

            if self.client:
                with self.client as client:
                    response = request.execute(client)
            else:
                response = request.execute()

            self.history.add(request, response)
            self.on_crawled(response)

            if self.delay_s:
                time.sleep(self.delay_s)


class HttpxCrawler(Crawler):
    client_type = httpx.Client
    cookies_type = httpx.Cookies

    def get_default_client(self):
        return httpx.Client()
