from scrupy import HttpxCrawler
from scrupy.request import CrawlResponse


class Crawler(HttpxCrawler):
    def on_crawled(self, response: CrawlResponse) -> None:
        # Set up the next iteration
        links = response.html.links
        if links:
            self.add_many_to_queue(links, ignore_repeated=True)

        # Save the html
        filename = response.request.url.replace('/', '_')

        with open(f'crawled/{filename}.html', 'w') as f:
            f.write(response.html.text)


crawler = Crawler(
    delay_per_request_ms=1000,
    urls=['https://wiki.python.org/moin/', ],

)

try:
    crawler.run()
except KeyboardInterrupt as e:
    print(crawler.history)
    raise e