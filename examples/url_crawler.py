from scrupy import HttpxCrawler
from scrupy.request import CrawlResponse


class Crawler(HttpxCrawler):
    def on_crawled(self, response: CrawlResponse) -> None:
        links = response.html.links
        self.add_many_to_queue(links, ignore_repeated=True)


crawler = Crawler(
    delay_per_request_ms=1000,
    urls=['https://www.python.org/doc/',]
)

crawler.run()
