class CrawlRequest:
    def __init__(self, url: str, method: str = 'GET', type: str = 'httpx'):
        self.url = url
        self.method = method
        self.type = type

    def execute(self):
        if self.type == 'httpx':
            import httpx
            exception = None
            response = None

            try:
                response = httpx.request(method=self.method, url=self.url)
            except Exception as e:
                exception = e
            return CrawlResponse(response=response, exception=exception, method=self.method)

    def __str__(self):
        return f'{self.__class__.__qualname__}(url={self.url}, method={self.method}, type={self.type})'

    def __repr__(self):
        return self.__str__()


class CrawlResponse:
    def __init__(self, *, response=None, exception: Exception, method: str):
        self.ok = response and not exception
        self.response = response
        self.exception = exception
        self.method = method

        self.status_code = getattr(response, 'status_code', None)
        self.http_version = getattr(response, 'status_code', None)
        self.request = getattr(response, 'request', None)

    @property
    def html(self):
        pass

    def __str__(self):
        return f'CrawlResponse(status_code={self.status_code}, exception={self.exception})'

    def __repr__(self):
        return self.__str__()
