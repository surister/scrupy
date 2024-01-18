import logging

from scrupy import HttpxCrawler, CrawlRequest
import redis

from scrupy.request import CrawlResponse

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)


class RedisCrawler(HttpxCrawler):
    def get_from_queue(self):
        logging.debug('Checking redis if url')
        return redis_client.rpop('url')

    def add_to_queue(self, url: CrawlRequest | str, add_left: bool = False):
        return redis_client.lpush('url', url)

    def on_crawled(self, response: CrawlResponse) -> None:
        logging.debug(f'Crawled response: {response}')

    def on_finish(self):
        return redis_client.close()

    def on_error(self, crawl_request):
        pass


redis_crawler = RedisCrawler(_delay_per_tick=1)
redis_crawler.run(run_forever=True)
