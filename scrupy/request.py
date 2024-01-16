import abc

UNSET = type('unset', (), {})


class CrawlRequestBase(abc.ABC):
    def __init__(self, url: str,
                 method: str = 'GET',
                 follow_redirect: UNSET = UNSET,
                 type: str = 'httpx'):
        self.url = url
        self.method = method
        # This allows us to have a default of False, and know when the
        # follow_redirect is directly passed in
        self.follow_redirect = follow_redirect
        self.type = type

    @abc.abstractmethod
    def _run_request(self, method, url, follow_redirect) -> object:
        ...

    @abc.abstractmethod
    def _build_response(self, request: 'CrawlRequestBase', response, exception: Exception,
                        method: str) -> 'CrawlResponse':
        ...

    def execute(self):
        exception = response = None
        self.follow_redirect = self.follow_redirect if self.follow_redirect is not UNSET else True

        try:
            response = self._run_request(
                method=self.method,
                url=self.url,
                follow_redirect=self.follow_redirect
            )

        except Exception as e:
            exception = e

        return self._build_response(
            request=self,
            response=response,
            exception=exception,
            method=self.method,
        )

    def __str__(self):
        return f'{self.__class__.__qualname__}(url={self.url}, method={self.method}, type={self.type})'

    def __repr__(self):
        return self.__str__()


class CrawlRequest(CrawlRequestBase):
    """
    Our default Crawl Request is httpx based.
    """

    def _run_request(self, method, url, follow_redirect) -> object:
        import httpx

        return httpx.request(
            method=self.method,
            url=self.url,
            follow_redirects=self.follow_redirect
        )

    def _build_response(self, request: 'CrawlRequestBase', response, exception: Exception,
                        method: str) -> 'CrawlResponse':
        return CrawlResponse(
            request=request,
            raw_response=response,
            exception=exception,
            method=method,
            status_code=getattr(response, 'status_code', None),
            http_version=getattr(response, 'http_version', None),
            raw_request=getattr(response, 'raw_request', None)
        )


class CrawlResponse:
    def __init__(self, *,
                 request: CrawlRequestBase,
                 raw_response=None,
                 exception: Exception,
                 method: str,
                 status_code: int,
                 http_version: str,
                 raw_request: object,
                 ):
        self.ok = raw_response and not exception
        self.raw_response = raw_response
        self.exception = exception
        self.method = method
        self.request = request

        self.status_code = status_code
        self.http_version = http_version
        self.raw_request = raw_request

    @property
    def html(self):
        pass

    def __str__(self):
        return f'CrawlResponse(status_code={self.status_code}, exception={self.exception})'

    def __repr__(self):
        return self.__str__()
