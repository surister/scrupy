import abc
import collections
import functools
import logging
import time
from collections import deque
from typing import Optional

import httpx

from .request import CrawlRequest, CrawlResponse
from .mixins import HTTPSettingAwareMixin
from .typing import SECONDS, MILLISECONDS

from fake_useragent import UserAgent

ua = UserAgent()
logger = logging.getLogger(__name__)


# logging.basicConfig(level=logging.DEBUG)


class CrawlHistory:
    def __init__(self):
        # Might want to use something more performant in the future, as lookups on runtime in the
        # history might become relevant to avoid repeated crawls, maybe a 'set' which has
        # Operation x in s
        # Average case O(1)
        # Worst Case O(n)
        self.skipped_disallowed = 0
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

    def exists(self, url: str):
        """
        Returns whether the given url exists in the history
        """
        for history_row in self.history:
            if history_row.request.url == url:
                return True
        return False

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


class CrawlerBase(HTTPSettingAwareMixin, abc.ABC):
    method: str = 'GET'

    def __init__(self,
                 *,
                 urls: Optional[list[str | CrawlRequest]] = None,
                 delay_per_request: MILLISECONDS = 1000,
                 follow_redirect: Optional[bool] = False,
                 min_delay_per_tick: MILLISECONDS = 0,
                 client=None,
                 user_agent: str = 'scrupy',
                 randomize_user_agent_per_request: bool = False,
                 headers: Optional[dict] = None,
                 timeout: Optional[SECONDS] = 5
                 ):
        self.urls: deque = deque(urls) if urls else deque()
        self.history = CrawlHistory()
        self.user_agent = user_agent
        self.timeout = timeout
        self.randomize_user_agent_per_request = randomize_user_agent_per_request

        self.headers = headers
        if self.headers is None:
            self.headers = {}

        self.follow_redirect = follow_redirect
        self.delay_per_request_s = delay_per_request // 1000
        self.min_delay_per_tick_s = min_delay_per_tick // 1000

        self._force_stop = False

        if client and not isinstance(client, getattr(self.__class__, 'client_type')):
            raise AttributeError('Wrong client type')  # Fix me improve exception

        self.client = client

    def add_many_to_queue(self,
                          urls: list[CrawlRequest | str],
                          add_left: bool = False,
                          ignore_repeated: bool = False) -> None:
        """
        Adds several elements to the crawling queue.

        If ignore_repeated is True, it will not add urls that were already crawled

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

        """
        if ignore_repeated:
            urls = set(urls) - set(map(lambda x: x.request.url, self.history))

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
        self.urls.appendleft(url) if add_left else self.urls.append(url)

    def get_from_queue(self):
        el = None
        try:
            el = self.urls.pop()
        except IndexError:  # Empty deque
            pass

        return el

    def on_crawled(self, response: CrawlResponse) -> None:
        pass

    def generate_user_agent(self, request) -> str:
        return ua.chrome

    def on_start(self) -> None:
        pass

    def on_finish(self) -> None:
        pass

    def on_check_if_allowed(self, request):
        return True

    @abc.abstractmethod
    def _run_request(self, request: CrawlRequest, client) -> object:
        ...

    @abc.abstractmethod
    def _build_response(self, request: CrawlRequest, raw_response,
                        exception: Optional[Exception]) -> CrawlResponse:
        ...

    @functools.cache
    @abc.abstractmethod
    def get_client(self) -> object:
        pass

    def _build_request(self, request: CrawlRequest | str) -> CrawlRequest:
        """
        Builds a request from the element got from the queue.

        Settings (ie: headers) from the queue (if it is already a CrawlRequest) are prioritized
        over wide Crawler settings.

        If a `client` is provided, the priority falls under the
        client's library implementation, in httpx, the default client the `fixme: FILL HERE`
        takes preferences.
        """

        if isinstance(request, str):
            request = CrawlRequest(request)

        # We put user_agent generation where since it might make sense to have
        # the request context when generating a request
        self.user_agent = self.generate_user_agent(request) if self.randomize_user_agent_per_request else self.user_agent

        request.inject_http_attrs_from(self)

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

    def force_stop(self) -> None:
        self._force_stop = True

    def run(self, run_forever: bool = False) -> None:
        """
        Initiates the crawling process:

        1. Gets a new element from the queue, we expect an url (str) or a CrawlRequest,
        if it is a string, it creates a `CrawlRequest` from it.
        2. Runs the request.
        3. Applies the configured delays
        """
        logger.debug(f'Start Crawler {self.__class__.__name__}')

        self.on_start()

        while run_forever or self.urls:
            now = time.time()
            next = self.get_from_queue()

            if next:
                request = self._build_request(next)

                is_allowed = self.on_check_if_allowed(request)

                if is_allowed:
                    self._crawl(request)

                else:
                    self.history.skipped_disallowed += 1
                    continue  # Skip the delays

            if self.delay_per_request_s:
                time.sleep(self.delay_per_request_s)

            if self._force_stop:
                break

            run_time = time.time() - now

            if run_time < self.min_delay_per_tick_s:
                time.sleep(self.min_delay_per_tick_s - run_time)

        self.on_finish()


class HttpxCrawler(CrawlerBase):
    client_type = httpx.Client
    cookies_type = httpx.Cookies

    def _run_request(self, request: CrawlRequest, client: httpx.Client) -> object:
        requester = client.request or httpx.request
        return requester(
            method=request.method,
            url=str(request.url),
            follow_redirects=request.follow_redirect,
            headers=self.headers,
            timeout=self.timeout,
        )

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
            headers=getattr(raw_response, 'headers', None),
            encoding=getattr(raw_response, 'default_encoding', None),
            text=getattr(raw_response, 'text', None),
        )

    def get_client(self):
        return self.client or httpx.Client()

    def on_finish(self) -> None:
        if self.client:
            self.client.close()
