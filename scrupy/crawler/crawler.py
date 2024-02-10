import datetime
import logging
import time
from typing import Optional

import httpx
import trio

from scrupy import CrawlRequest
from scrupy.crawler.base import CrawlerBase
from scrupy.crawler.frontier import AsyncFrontier, SyncFrontier
from scrupy.request import CrawlResponse

logger = logging.getLogger(__name__)


class SyncCrawler(CrawlerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontier = SyncFrontier()

    def add_to_queue(self, urls: list[CrawlRequest | str], ignore_repeated: bool = False) -> None:
        requests = [self._build_request(req_or_str) for req_or_str in self.start_urls]
        if ignore_repeated:
            requests = set(urls) - set(map(lambda x: x.request.url, self.history))

        self.frontier.add_to_queue(requests)

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

    def get_next(self):
        return self.frontier.get_next()

    def run(self, run_forever: bool = False) -> None:
        """
        Initiates the crawling process:
        """
        logger.debug(f'Start Crawler {self.__class__.__name__}')

        self.on_start()

        while run_forever or self.urls:
            now = time.time()
            next = self.get_from_queue()

            if next:
                is_allowed = self.on_check_if_allowed(next)

                if is_allowed:
                    self._crawl(next)

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


class AsyncCrawler(CrawlerBase):
    def __init__(
            self,
            start_urls: Optional[str | CrawlRequest] = None,
            randomize_user_agent_per_request: bool = False,
            user_agent: str = 'scrupy',
    ):
        super().__init__()
        self.start_urls = start_urls
        self.randomize_user_agent_per_request = randomize_user_agent_per_request
        self.user_agent = user_agent
        self.frontier = AsyncFrontier()

    async def add_to_queue(self, urls: list[CrawlRequest | str],
                           ignore_repeated: bool = False) -> None:
        requests = [self._build_request(req_or_str) for req_or_str in self.start_urls]
        logger.debug(f'Adding {requests} to frontier')
        await self.frontier.add_to_queue(requests)

    async def on_crawled(self, response: CrawlResponse) -> None:
        pass

    async def on_finish(self) -> None:
        pass

    async def on_start(self) -> None:
        pass

    def get_next(self):
        raise Exception('Async does not use get_next')

    async def crawl_task(self, nursery, receive_channel):
        async for request in receive_channel:
            nursery.start_soon(self._crawl, request)

    async def _run_request(self, request: CrawlRequest, client: httpx.AsyncClient) -> object:
        return await client.request(
            method=request.method,
            url=str(request.url),
            follow_redirects=request.follow_redirect,
            headers=self.headers,
            timeout=self.timeout,
        )

    async def _crawl(self, request: CrawlRequest):
        client = self.get_client()

        raw_response = exception = None

        if self.frontier.delay_rules.get_delay(request.url.domain):
            self.frontier.queue[request.url.domain]['last_crawled'] = time.time()

        try:
            raw_response = await self._run_request(request, client)
        except Exception as e:
            exception = e

        response = self._build_response(
            request=request,
            raw_response=raw_response,
            exception=exception,
        )

        self.history.add(request, response, datetime.datetime.now())
        await self.on_crawled(response)

    def run(self, run_forever: bool = False) -> None:
        async def _run():
            if self.start_urls:
                await self.add_to_queue(self.start_urls)

            async with trio.open_nursery() as nursery:
                nursery.start_soon(self.frontier.run)
                nursery.start_soon(self.crawl_task, nursery, self.frontier.receive_channel)

                while True:
                    await trio.sleep(1)
                    if (
                            not run_forever
                            and len(nursery.child_tasks) == 2
                            and self.frontier.pending_requests == 0
                    ):
                        nursery.cancel_scope.cancel()
                        await self.on_finish()

        trio.run(_run)


class HttpxCrawler(SyncCrawler):
    client_type = httpx.Client
    cookies_type = httpx.Cookies

    def _run_request(self, request: CrawlRequest, client: httpx.Client) -> object:
        return client.request(
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

        super().on_finish()


class AsyncHttpxCrawler(AsyncCrawler):
    client_type = httpx.AsyncClient
    cookies_type = httpx.Cookies

    def get_client(self) -> httpx.AsyncClient:
        return self.client or httpx.AsyncClient()

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
