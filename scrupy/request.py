class unset:
    """
    Sentinel object singleton to describe a parameter that has not been explicitly set by the user
    """

    def __bool__(self):
        raise Exception("Don't use boolean operators for unset, check identity with 'is', ie: myvar is UNSET")

    def __repr__(self):
        return str(self.__class__)


UNSET = unset()


class CrawlRequest:
    def __init__(self,
                 url: str,
                 method: str = 'GET',
                 follow_redirect: UNSET = UNSET,
                 headers: UNSET = UNSET,
                 type: str = 'httpx'):
        self.url = url
        self.method = method
        self.headers = headers
        self.follow_redirect = follow_redirect
        self.type = type

    def __str__(self):
        return f'{self.__class__.__qualname__}(url={self.url}, method={self.method}, type={self.type})'

    def __repr__(self):
        return self.__str__()


class CrawlResponse:
    def __init__(self,
                 *,
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
