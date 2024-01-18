import abc
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


class CrawlerBase(abc.ABC):
    method: str = 'GET'
    urls: deque[CrawlRequest] = deque()
    history = CrawlHistory()

    def __init__(self,
                 *,
                 delay_s: int = None,
                 follow_redirect: Optional[bool] = False,
                 client=None,
                 ):
        self.delay_s = delay_s
        self.follow_redirect = follow_redirect

        if client and not isinstance(client, getattr(self.__class__, 'client_type')):
            raise AttributeError('Wrong client type')  # Improve exception

        self.client = client

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

    def get_client(self) -> object:
        pass

    def _get_extra_opts(self):
        return {
            'follow_redirects': self.follow_redirect
        }

    @abc.abstractmethod
    def _run_request(self, request: CrawlRequest, client) -> object:
        ...

    @abc.abstractmethod
    def _build_response(self, request: CrawlRequest, raw_response, exception: Optional[Exception]) -> CrawlResponse:
        ...

    # @finally('close_connection_pool')
    def crawl(self) -> None:
        """
        Initiates the crawling process, gets a CrawlRequest from the queue, creates all the necessary objects/conf,
        runs it and adds it to history.
        """
        while self.urls:
            raw_response = exception = None

            # request always refers to CrawlRequest objects, and raw_request, to whatever underlining request object
            # gets created, ie: requests.Request, httpx.Request..
            request = self.get_from_queue()
            client = self.get_client()

            try:
                raw_response = self._run_request(request, client)

            except Exception as e:
                exception = e

            response = self._build_response(
                request=request,
                raw_response=raw_response,
                exception=exception,
            )

            # if self.follow_redirect is not None and request.follow_redirect is UNSET:
            #     # Priority is: CrawlRequest passed settings > Crawler settings
            #     request.follow_redirect = self.follow_redirect

            # if self.client:
            #     with self.client as client:
            #         response = request.execute(client)
            # else:
            #     response = request.execute()

            self.history.add(request, response)
            self.on_crawled(response)

            if self.delay_s:
                time.sleep(self.delay_s)


class HttpxCrawler(CrawlerBase):
    client_type = httpx.Client
    cookies_type = httpx.Cookies

    def _close_connection_pool(self, client: httpx.Client) -> None:
        client.close()

    def _run_request(self, request: CrawlRequest, client: httpx.Client) -> object:
        opts = self._get_extra_opts()

        if request.follow_redirects is UNSET:
            request.follow_redirects = opts.get('follow_redirects')

        requester = client.request or httpx.request
        return requester(request.method, request.url, follow_redirects=request.follow_redirects)

    def _build_response(self,
                        request: CrawlRequest,
                        raw_response: httpx.Response,
                        exception: Optional[Exception] = None) -> CrawlResponse:
        return CrawlResponse(
            request=request,
            raw_response=raw_response,
            exception=exception,
            status_code=getattr(raw_response, 'status_code', None),
            method=getattr(raw_response, 'request.method', None),
            http_version=getattr(raw_response, 'http_version', None),
        )

    def get_client(self):
        return self.client or httpx.Client()
