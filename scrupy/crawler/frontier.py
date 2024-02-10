import abc
import collections
import logging
import math
import time
import typing

import trio

from ..request import CrawlRequest

RoutingRules = type('RoutingRules', (), {})

logger = logging.getLogger('Frontier')


class FrontierBase(abc.ABC):

    @abc.abstractmethod
    def add_to_queue(self, requests: list[CrawlRequest]):
        ...

    @abc.abstractmethod
    def get_next(self) -> typing.Optional[CrawlRequest]:
        ...

    @abc.abstractmethod
    def exists_in_queue(self, domain: str):
        ...


class SyncFrontier(FrontierBase):
    def __init__(self, requests: list[CrawlRequest] = None):
        if not requests:
            requests = []

        self.queue = collections.deque(requests)

    def get_next(self) -> typing.Optional[CrawlRequest]:
        el = None

        try:
            el = self.queue.pop()
        except IndexError:  # Empty deque
            pass

        return el

    def add_to_queue(self, requests: list[CrawlRequest]):
        self.queue.extend(requests)

    def exists_in_queue(self, domain: str):
        return domain in self.queue


class AsyncFrontier(FrontierBase):
    def __init__(self, delay_rules: typing.Optional[RoutingRules] = None):
        if not delay_rules:
            RoutingRules.get_delay = lambda a, _: 1

        self.delay_rules = RoutingRules()
        self._send_channel, self._receive_channel = trio.open_memory_channel(math.inf)
        self.pending_requests = 0
        """
        Queue is structured by domain, ie:
        
        {
            "www.example.com": {
                "requests": req1, req2, req3,
                "last_crawled_time": 2394892338
            },
            "another_domain.de": {
                ...
            }
        }
        
        Where:
         - 'requests' is the pending requests.
         - 'last_crawled_time' is the last time a CrawlRequest was started in unix time, we count the delay
         from this moment.
        """
        self.queue = {}

    def _add_to_queue(self, request: CrawlRequest) -> bool:
        # Can we simplify all of this with just a defaultdict? fixme
        self.pending_requests += 1

        if self.exists_in_queue(request.url.domain):
            self.queue[request.url.domain].get('requests').append(request)
            return False

        self.queue[request.url.domain] = {
            'last_crawled': None,
            'requests': collections.deque()
        }
        return True

    async def add_to_queue(self, requests: list[CrawlRequest]):
        for request in requests:
            delay = self.delay_rules.get_delay(request.url.domain)
            if delay:
                first_added = self._add_to_queue(request)
                if first_added:
                    self.pending_requests -= 1
                    await self.send_channel.send(request)
            else:
                await self.send_channel.send(request)

    def exists_in_queue(self, domain: str):
        return domain in self.queue

    def get_next(self) -> typing.Optional[CrawlRequest]:
        raise NotImplementedError(
            '`get_next` can only be used with `SyncCrawler`,'
            ' in `AsyncCrawler` to get the next available request read from `receive_channel`'
        )

    @property
    def send_channel(self):
        return self._send_channel

    @property
    def receive_channel(self):
        return self._receive_channel

    async def run(self) -> None:
        while True:
            await trio.sleep(.1)

            for _, v in self.queue.items():
                queue_by_domain = v.get('requests')

                if not queue_by_domain:
                    # Empty queue, nothing to evaluate.
                    continue

                last_crawled = v.get('last_crawled')
                if not last_crawled:
                    # There is a CrawlRequest of the same queue already sent and has not been
                    # executed yet, therefore, it doesn't have last_crawled, in that case
                    # we shouldn't schedule a new one, or we wouldn't be respecting the delays.
                    continue

                next_request = queue_by_domain[0]  # Peek the deque.
                logger.debug(f'Checking next request: {next_request}')

                if time.time() - last_crawled >= self.delay_rules.get_delay(
                        next_request.url.domain):
                    self.pending_requests -= 1

                    await self.send_channel.send(queue_by_domain.pop())
