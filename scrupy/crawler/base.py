import abc
import functools
import logging
from typing import Optional

from fake_useragent import UserAgent

from scrupy import CrawlRequest
from scrupy.crawler.history import CrawlHistory
from scrupy.mixins import HTTPSettingAwareMixin
from scrupy.request import CrawlResponse
from scrupy.typing import MILLISECONDS, SECONDS

ua = UserAgent()

logger = logging.getLogger(__name__)


class CrawlerBase(HTTPSettingAwareMixin, abc.ABC):
    method: str = 'GET'

    def __init__(self,
                 *,
                 start_urls: Optional[list[str]] = None,
                 delay_per_request: MILLISECONDS = 1000,
                 follow_redirects: Optional[bool] = False,
                 min_delay_per_tick: MILLISECONDS = 0,
                 client=None,
                 user_agent: str = 'scrupy',
                 randomize_user_agent_per_request: bool = False,
                 headers: Optional[dict] = None,
                 timeout: Optional[SECONDS] = 5
                 ):
        self.start_urls = start_urls
        self.user_agent = user_agent
        self.timeout = timeout
        self.randomize_user_agent_per_request = randomize_user_agent_per_request

        self.headers = headers
        if self.headers is None:
            self.headers = {}

        self.follow_redirects = follow_redirects
        self.delay_per_request_s = delay_per_request // 1000
        self.min_delay_per_tick_s = min_delay_per_tick // 1000

        self._force_stop = False
        self.client = client

    @abc.abstractmethod
    def add_to_queue(self, urls: list[str] | str) -> None:
        ...

    @abc.abstractmethod
    def get_next(self):
        ...

    @functools.cached_property
    def history(self) -> CrawlHistory:
        return CrawlHistory()

    def generate_user_agent(self, request) -> str:
        return ua.chrome

    @abc.abstractmethod
    def on_crawled(self, response: CrawlResponse) -> None:
        ...

    def on_before_crawl(self, request: CrawlRequest) -> CrawlRequest:
        return request

    def on_start(self) -> None:
        self.client.on_start()

    @abc.abstractmethod
    def on_finish(self) -> None:
        ...

    def on_check_if_allowed(self, request):
        return True

    def _build_request(self, url: str) -> CrawlRequest:
        if not isinstance(url, str):
            raise TypeError(f'Expected `str` got {type(url)}')

        request = CrawlRequest(url)

        # We put user_agent generation here since it might make sense to have
        # the request context when generating a request
        self.user_agent = self.generate_user_agent(
            request) if self.randomize_user_agent_per_request else self.user_agent

        request.inject_http_attrs_from(self)

        return request

    @abc.abstractmethod
    def _crawl(self, request: CrawlRequest) -> None:
        ...

    def force_stop(self) -> None:
        self._force_stop = True

    @abc.abstractmethod
    def run(self, run_forever: bool = False) -> None:
        ...


class CrawlerClientBase(abc.ABC):
    @abc.abstractmethod
    def run_request(self, request, client):
        ...

    @abc.abstractmethod
    def build_response(self,
                       request: CrawlRequest,
                       raw_response,
                       exception: Optional[Exception] = None) -> CrawlResponse:
        ...

    @abc.abstractmethod
    def get_new_client(self):
        pass

    def cleanup(self) -> None:
        pass

    def on_start(self) -> None:
        ...
