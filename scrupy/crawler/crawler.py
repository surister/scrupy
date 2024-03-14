import abc
import datetime
import logging
import time
from typing import Optional

import httpx
import trio
import trio_asyncio

from scrupy import CrawlRequest
from scrupy.crawler.base import CrawlerBase, CrawlerClientBase
from scrupy.crawler.clients import HttpxClient, AsyncHttpxClient
from scrupy.crawler.frontier import AsyncFrontier, SyncFrontier
from scrupy.request import CrawlResponse

logger = logging.getLogger(__name__)


class Crawler(CrawlerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frontier = SyncFrontier()
        self._crawl_client = HttpxClient()

        if self.start_urls:
            self.add_to_queue(self.start_urls)

    def add_to_queue(self,
                     urls: list[str] | str | CrawlRequest,
                     ignore_repeated: bool = False) -> None:
        match urls:
            case str():
                urls = (urls,)

        requests = [self._build_request(url) for url in urls]

        if ignore_repeated:
            requests = set(urls) - set(map(lambda x: x.request.url, self.history))

        self.frontier.add_to_queue(requests)

    def _crawl(self, request: CrawlRequest) -> None:
        request = self.on_before_crawl(request)

        raw_response = exception = None
        client = self.client or self._crawl_client.get_new_client()

        try:
            raw_response = self._crawl_client.run_request(request, client)

        except Exception as e:
            exception = e

        response = self._crawl_client.build_response(
            request=request,
            raw_response=raw_response,
            exception=exception,
        )

        self.history.add(request, response, datetime.datetime.now())
        self.on_crawled(response)

    def get_next(self):
        return self.frontier.get_next()

    def on_crawled(self, response: CrawlResponse) -> None:
        pass

    def on_finish(self) -> None:
        pass

    def on_start(self) -> None:
        pass

    def run(self, run_forever: bool = False) -> None:
        """
        Initiates the crawling process:
        """
        logger.debug(f'Start Crawler {self.__class__.__name__}')
        self.on_start()

        while run_forever or len(self.frontier):
            now = time.time()
            next = self.get_next()

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
            start_urls: Optional[list[str | CrawlRequest]] = None,
            randomize_user_agent_per_request: bool = False,
            user_agent: str = 'scrupy',
    ):
        super().__init__()
        self.start_urls = start_urls
        self.randomize_user_agent_per_request = randomize_user_agent_per_request
        self.user_agent = user_agent
        self.frontier = AsyncFrontier()
        self._crawl_client = AsyncHttpxClient()

    async def add_to_queue(self, urls: list[CrawlRequest | str],
                           ignore_repeated: bool = False) -> None:
        requests = [self._build_request(req_or_str) for req_or_str in self.start_urls]
        logger.debug(f'Adding {requests} to frontier')
        await self.frontier.add_to_queue(requests)

    async def on_crawled(self, response: CrawlResponse) -> None:
        pass

    async def on_finish(self) -> None:
        print('closin')
        await self.client.close()

    async def on_start(self) -> None:
        ...

    def get_next(self):
        raise Exception('Async does not use get_next')

    async def crawl_task(self, nursery, receive_channel):
        async for request in receive_channel:
            nursery.start_soon(self._crawl, request)

    async def _crawl(self, request: CrawlRequest):
        raw_response = exception = None

        if self.frontier.delay_rules.get_delay(request.url.domain):
            self.frontier.queue[request.url.domain]['last_crawled'] = time.time()

        try:
            raw_response = await self._crawl_client.run_request(request, self.client)
        except Exception as e:
            exception = e

        response = self._crawl_client.build_response(
            request=request,
            raw_response=raw_response,
            exception=exception,
        )

        self.history.add(request, response, datetime.datetime.now())
        await self.on_crawled(response)

    def run(self, run_forever: bool = False) -> None:
        async def _run():
            self.client = await self._crawl_client.get_new_client()

            if self.start_urls:
                await self.add_to_queue(self.start_urls)

            async with trio.open_nursery() as nursery:
                await self.on_start()
                nursery.start_soon(self.frontier.run)
                nursery.start_soon(self.crawl_task, nursery, self.frontier.receive_channel)

                while True:
                    await trio.sleep(.75)
                    if (
                            not run_forever
                            and len(nursery.child_tasks) == 2  # No current running crawl requests
                            and self.frontier.pending_requests == 0  # No pending crawl requests
                    ):
                        nursery.cancel_scope.cancel()
                        await self.on_finish()

        trio_asyncio.run(_run)
