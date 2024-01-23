import pytest

from scrupy import CrawlRequest


@pytest.fixture
def crawl_request():
    return CrawlRequest(
        url='https://www.myfixtureurl.com',
    )
