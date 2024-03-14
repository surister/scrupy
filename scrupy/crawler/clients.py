import logging
from collections import namedtuple
from typing import Optional, NamedTuple

import httpx
import playwright
import trio_asyncio
from playwright.async_api import async_playwright, PlaywrightContextManager

from scrupy import CrawlRequest
from scrupy.crawler.base import CrawlerClientBase
from scrupy.request import CrawlResponse


class HttpxClient(CrawlerClientBase):
    client_type = httpx.Client
    cookies_type = httpx.Cookies

    def run_request(self, request: CrawlRequest, client: httpx.Client):
        return client.request(
            method=request.method,
            url=str(request.url),
            follow_redirects=request.follow_redirects,
            headers=request.headers,
            timeout=request.timeout,
        )

    def build_response(self,
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

    def get_new_client(self):
        return httpx.Client()

    def on_finish(self) -> None:
        if self.client:
            self.client.close()

        super().on_finish()


class AsyncPlaywrightClient(CrawlerClientBase):
    client_type = None
    cookies_type = None

    @trio_asyncio.aio_as_trio
    async def get_new_client(self):
        pw = await PlaywrightContextManager().start()
        firefox = pw.firefox
        browser = await firefox.launch(headless=True)

        await pw.stop()  # <- This has to be somehow called when ending the session
        # browser.stop = trio_asyncio.aio_as_trio(browser.stop)
        # we should stop the pw, not the browser per se because Browser has no attribute stop
        return browser

    @trio_asyncio.aio_as_trio
    async def run_request(self, request, client):
        browser = client

        await browser.new_context()
        page = await browser.new_page()

        response = await page.goto(str(request.url))
        await page.wait_for_load_state('domcontentloaded')
        await page.wait_for_timeout(450)

        content = await page.content()
        await browser.close()
        return namedtuple('Response',
                          ['status_code', 'http_version', 'headers', 'text', 'encoding'])(
            status_code=response.status,
            http_version='unknown',
            headers=response.headers,
            text=content,
            encoding='unknown'
        )

    async def cleanup(self) -> None:
        pass

    async def on_start(self) -> None:
        print('starting!')

    def build_response(self,
                       request: CrawlRequest,
                       raw_response,
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


class AsyncHttpxClient(CrawlerClientBase):
    client_type = httpx.AsyncClient
    cookies_type = httpx.Cookies

    def get_new_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient()

    async def run_request(self, request: CrawlRequest, client: httpx.AsyncClient) -> object:
        return await client.request(
            method=request.method,
            url=str(request.url),
            follow_redirects=request.follow_redirects,
            headers=request.headers,
            timeout=request.timeout,
        )

    def build_response(self,
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
