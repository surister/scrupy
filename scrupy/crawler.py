import abc
import collections
import logging
import time
from collections import deque
from typing import Optional

import httpx

from .request import CrawlRequest, CrawlResponse, UNSET

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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
                 delay_per_request_ms: int = 0,
                 follow_redirect: Optional[bool] = False,
                 min_delay_per_tick_ms: int = 500,
                 client=None,
                 ):
        self.follow_redirect = follow_redirect
        self.delay_per_request_s = delay_per_request_ms // 1000
        self.min_delay_per_tick_s = min_delay_per_tick_ms // 1000

        self._force_stop = False

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
            url = CrawlRequest(url)  # Fixme Can probably delete this conditional
        self.urls.appendleft(url) if add_left else self.urls.append(url)

    def get_from_queue(self):
        el = None
        try:
            el = self.urls.pop()
        except IndexError: # Empty deque
            pass

        return el

    def on_crawled(self, response: CrawlResponse) -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_finish(self) -> None:
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

    @abc.abstractmethod
    def get_client(self) -> object:
        pass

    def _build_request(self, request: CrawlRequest | str) -> CrawlRequest:
        if isinstance(request, str):
            request = CrawlRequest(request)

        if request.follow_redirect is UNSET:
            request.follow_redirect = self.follow_redirect

        return request

    def _crawl(self, request: CrawlRequest) -> None:
        raw_response = exception = None

        try:
            raw_response = self._run_request(request, self.get_client())

        except Exception as e:
            exception = e

        response = self._build_response(
            request=request,
            raw_response=raw_response,
            exception=exception,
        )

        self.history.add(request, response)
        self.on_crawled(response)

    def force_stop(self):
        self._force_stop = True

    def run(self, run_forever: bool = False) -> None:
        """
        Initiates the crawling process, gets a CrawlRequest from the queue, creates all the necessary objects/conf,
        runs it and adds it to history.
        """
        logger.debug(f'Start Crawler {self.__class__.__name__}')

        self.on_start()

        while run_forever or self.urls:
            _now = time.time()
            request = self.get_from_queue()

            if isinstance(request, str):
                ...  # TODO Move all str --> CrawlRequest builds here.

            if request:
                self._crawl(request)

            if self.delay_per_request_s:
                time.sleep(self.delay_per_request_s)

            if self._force_stop:
                break

            _run_time = time.time() - _now

            if _total_delay := _run_time + (self.delay_per_request_s or 0) < self.min_delay_per_tick_s:
                # min delay per tick does not seem to work
                time.sleep(_total_delay - self.min_delay_per_tick_s)

        self.on_finish()


class HttpxCrawler(CrawlerBase):
    client_type = httpx.Client
    cookies_type = httpx.Cookies

    def _run_request(self, request: CrawlRequest, client: httpx.Client) -> object:
        opts = self._get_extra_opts()

        if request.follow_redirect is UNSET:
            request.follow_redirect = opts.get('follow_redirects')

        requester = client.request or httpx.request
        return requester(request.method, request.url, follow_redirects=request.follow_redirect)

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

    def on_finish(self) -> None:
        if self.client:
            self.client.close()
