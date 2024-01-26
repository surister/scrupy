from scrupy.request import CrawlResponse, HtmlParser


def test_response_json(crawl_request):
    response = CrawlResponse(
        request=crawl_request,
        raw_response=object,
        exception=None,
        method='GET',
        status_code=200,
        http_version='http/1.1',
        headers={
            'content-type': 'application/json'
        },
        text="""
        {
            "response": 200
        }
        """,
    )
    assert response.is_json
    assert isinstance(response.json, dict)
    assert response.json['response'] == 200
    assert response.request == crawl_request
    assert not response.html


def test_response_html(crawl_request):
    url = 'https://example.com'
    response = CrawlResponse(
        request=crawl_request,
        raw_response=object,
        exception=None,
        method='GET',
        status_code=200,
        http_version='http/1.1',
        headers={
            'content-type': 'text/html'
        },
        text=f"""
            <!DOCTYPE html>
            <html>
                <head></head>
                <body>
                <li>
                <a href="{url}">my link</a>
                </li>
                    <!-- the content goes here -->
                </body>
            </html>
        """,
    )
    assert response.is_html
    assert isinstance(response.html, HtmlParser)
    assert response.request == crawl_request
    assert not response.is_json
    assert not response.json

    assert len(list(response.html.links)) == 1
    assert list(response.html.links)[0] == url

    response.text = ""

    assert not list(response.html.links)  # No links but it doesn't blow.
