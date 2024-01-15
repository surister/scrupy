from request import CrawlRequest


class CrawlHistory:
    def __init__(self):
        self.history = []
        self.i = 0

    def add(self, request: CrawlRequest, response: CrawlResponse):
        self.history.append(
            {
                'id': self.i,
                'url': request.url,
                'method': response.method,
                'response': response,
                'status_code': response.status_code,
                'http_version': response.http_version,
                'exception': response.exception
            }
        )

        self.i += 1

    def __iter__(self):
        return iter(self.history)

    def __str__(self):
        return str(self.history)

    def __repr__(self):
        return self.__str__()


class Crawler:
    method: str = 'GET'
    queue: deque[CrawlRequest] = deque()
    history = CrawlHistory()

    def __init__(self, *, delay_s: int = None):
        self.delay_s = delay_s

    def add_many_to_queue(self, urls: list[CrawlRequest | str], add_left: bool = False):
        """
        Adds several elements to the crawling queue.

        Add a list of CrawlRequest
            >>> requests = [
            >>> CrawlRequest(url='https://www.google.com', method=POST),
            >>> CrawlRequest(url='https://www.reddit.com', method=GET),
            >>> CrawlRequest(url='https://www.google.co.uk', method=POST)
            >>> ]
            >>> Crawler.add_to_queue(requests)



            Add a list of urls
            >>> Crawler.add_to_queue(
            >>> ['https://www.google.com', 'https://www.reddit.com', 'https://www.linkedin.com']
            >>> )

        :param urls:
        :param add_left:
        :return:
        """
        if isinstance(urls[0], str):
            urls = [CrawlRequest(url=url) if isinstance(url, str) else url for url in urls]

        self.queue.extendleft(urls) if add_left else self.queue.extend(urls)

    def add_to_queue(self, url: CrawlRequest | str, add_left: bool = False) -> None:
        """
        Adds a new CrawlRequest to the queue.

        Examples:

            Add one new CrawlRequest
            >>> new_request = CrawlRequest(url='https://www.google.com', method=POST)
            >>> Crawler.add_to_queue(new_request)

            Add one new url
            >>> Crawler.add_to_queue('https://www.google.com')
        """

        if isinstance(url, str):
            url = CrawlRequest(url)
        self.queue.appendleft(url) if add_left else self.queue.append(url)

    def on_crawled(self, response: CrawlResponse) -> None:
        pass

    def crawl(self) -> None:
        while self.queue:
            request = self.queue.pop()
            response = request.execute()

            self.history.add(request, response)
            self.on_crawled(response)

            if self.delay_s:
                time.sleep(self.delay_s)
