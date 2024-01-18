class unset:
    def __bool__(self):
        return False

    def __repr__(self):
        return str(self.__class__)


UNSET = unset()


class CrawlRequest:
    def __init__(self,
                 url: str,
                 method: str = 'GET',
                 follow_redirects: UNSET = UNSET,
                 type: str = 'httpx'):
        self.url = url
        self.method = method
        # This allows us to have a default of False, and know when the
        # follow_redirect is directly passed in
        self.follow_redirects = follow_redirects
        self.type = type

    def __str__(self):
        return f'{self.__class__.__qualname__}(url={self.url}, method={self.method}, type={self.type})'

    def __repr__(self):
        return self.__str__()


class CrawlResponse:
    def __init__(self, *,
                 request: CrawlRequest,
                 raw_response=None,
                 exception: Exception,
                 method: str,
                 status_code: int,
                 http_version: str,
                 ):
        self.ok = raw_response and not exception
        self.raw_response = raw_response
        self.exception = exception
        self.method = method
        self.request = request

        self.status_code = status_code
        self.http_version = http_version

    @property
    def html(self):
        pass

    def __str__(self):
        return f'CrawlResponse(status_code={self.status_code}, exception={self.exception})'

    def __repr__(self):
        return self.__str__()
