from typing import Optional

import httpx

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
            headers=self.headers,
            timeout=self.timeout,
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
