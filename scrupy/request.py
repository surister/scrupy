import json
from typing import Optional

from .typing import SECONDS
from .utils import UNSET, Url
from .mixins import HTTPSettingAwareMixin


class CrawlRequest(HTTPSettingAwareMixin):
    def __init__(self,
                 url: str,
                 method: str = 'GET',
                 follow_redirect: UNSET = UNSET,
                 user_agent: UNSET = UNSET,
                 headers: UNSET = UNSET,
                 timeout: SECONDS = 5,
                 type: str = 'httpx'):
        self.url = Url(url)
        self.method = method
        self.headers = headers
        self.user_agent = user_agent
        self.follow_redirect = follow_redirect
        self.timeout = timeout
        self.type = type

    def __str__(self):
        return f'{self.__class__.__qualname__}(url={self.url}, method={self.method}, type={self.type})'

    def __repr__(self):
        return self.__str__()


class HtmlParser:
    def __init__(self, html: str, text: str, tag: str, attributes: Optional[dict] = None):
        self.html = html
        self.text = text
        self.tag = tag

        self.attributes = attributes
        if not self.attributes:
            self.attributes = {}

    def selectolax(self):
        try:
            import selectolax
        except ImportError:
            raise Exception('selectolax is not installed')
        return selectolax.parser.HTMLParser(self.html)

    def find(self, selector: str, first=False) -> list['HtmlParser']:
        function = self.selectolax().css_first if first else self.selectolax().css
        from collections.abc import Iterable

        res = function(selector)
        if not isinstance(res, Iterable):
            res = (res,)
        res = [
            HtmlParser(
                html=el.html,
                attributes=el.attributes,
                tag=el.tag,
                text=el.text()
            ) for el in res
        ]
        return res

    @property
    def links(self):
        if not self.html:
            return list()

        return [a_tag.attributes.get('href') for a_tag in self.selectolax().css('a')]

    def attr(self, attr_name, default_val=None):
        return self.attributes[attr_name]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        f = False
        pos = 0
        for i, char in enumerate(self.html):
            if char == '<':
                f = True
                pos = i
            if f and char == '>':
                return f'Node {self.html[pos: i + 1]}'


class CrawlResponse:
    def __init__(self,
                 *,
                 request: CrawlRequest,
                 raw_response=None,
                 exception: Optional[Exception],
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
        return json.loads(self.text) if self.is_json else None

    @property
    def is_html(self):
        if not self.headers:
            self.headers = {}
        content_type_header = self.headers.get('content-type', None)
        if content_type_header:
            return 'text/html' in content_type_header
        return False

    @property
    def html(self) -> Optional[HtmlParser]:
        return HtmlParser(self.text, attributes=None, tag='html', text='') if self.is_html else None

    def __str__(self):
        return f'CrawlResponse(status_code={self.status_code}, exception={self.exception})'

    def __repr__(self):
        return self.__str__()
