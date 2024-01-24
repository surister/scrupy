import json
from typing import Optional
from functools import lru_cache

from .utils import UNSET
from .mixins import HTTPSettingAwareMixin


class CrawlRequest(HTTPSettingAwareMixin):
    def __init__(self, url: str, method: str = 'GET', follow_redirect: UNSET = UNSET,
                 user_agent: UNSET = UNSET, headers: UNSET = UNSET, type: str = 'httpx'):

        self.url = url
        self.method = method
        self.headers = headers
        self.user_agent = user_agent
        self.follow_redirect = follow_redirect
        self.type = type

    def __str__(self):
        return f'{self.__class__.__qualname__}(url={self.url}, method={self.method}, type={self.type})'

    def __repr__(self):
        return self.__str__()


class HtmlParser:
    def __init__(self, text):
        self.text = text

    @property
    @lru_cache
    def soup(self):
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise Exception('BeautifulSoup is not installed')
        return BeautifulSoup(self.text, 'lxml')

    @property
    def lxml(self):
        try:
            import lxml
        except ImportError:
            raise Exception('lxml is missing')
        return lxml.etree(self.text)

    @property
    def links(self, only_https: bool = False):
        if not self.text:
            return list()

        scheme = 'https' if only_https else 'http'

        for a in self.soup.find_all('a'):
            link = a.get('href')
            if link and scheme in link:
                yield link

    def __str__(self):
        return self.text


class CrawlResponse:
    def __init__(self,
                 *,
                 request: CrawlRequest,
                 raw_response=None,
                 exception: Exception,
                 method: str,
                 status_code: int,
                 http_version: str,
                 headers: dict,
                 text: Optional[str] = None,
                 encoding: str = 'utf-8'
                 ):
        self.ok = raw_response and not exception
        self.raw_response = raw_response
        self.exception = exception
        self.method = method
        self.request = request

        self.status_code = status_code
        self.http_version = http_version
        self.headers = headers

        self.text = text

        self.encoding = encoding

    @property
    def is_json(self) -> bool:
        return 'application/json' in self.headers['content-type']

    @property
    def json(self) -> list | dict:
        return json.loads(self.text)

    @property
    def html(self) -> HtmlParser:
        return HtmlParser(self.text)

    def __str__(self):
        return f'CrawlResponse(status_code={self.status_code}, exception={self.exception})'

    def __repr__(self):
        return self.__str__()
