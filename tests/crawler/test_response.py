from scrupy.request import HtmlParser


def test_response_json(crawl_request, successful_response):
    successful_response.headers = {
        'content-type': 'application/json'
    }
    successful_response.text = """
        {
            "response": 200
        }
        """
    successful_response.request = crawl_request
    response = successful_response

    assert response.is_json
    assert isinstance(response.json, dict)
    assert response.json['response'] == 200
    assert response.request == crawl_request
    assert not response.html


def test_response_html(crawl_request, successful_response):
    url = 'https://example.com'
    successful_response.headers = {
        'content-type': 'text/html'
    }
    successful_response.text = f"""
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
        """
    successful_response.request = crawl_request
    response = successful_response

    assert response.is_html
    assert isinstance(response.html, HtmlParser)
    assert response.request == crawl_request
    assert not response.is_json
    assert not response.json


def test_response_html_links(crawl_request, successful_response):
    url = 'https://example.com'
    successful_response.headers = {
        'content-type': 'text/html'
    }
    successful_response.text = f"""
            <!DOCTYPE html>
            <html>
                <head class="what"></head>
                <body>
                    <div class="container">
                        <h1 id="myid">Title</h1>
                        <a href="{url}"></a>
                        <a href="http://localhost.com"></a>
                    </div>
                </body>
            </html>
        """
    successful_response.request = crawl_request
    response = successful_response

    assert len(response.html.links) == 2
    assert list(response.html.links)[0] == url

    response.text = ""

    assert not response.html.links


def test_response_html_selects(crawl_request, successful_response):
    url = 'https://example.com'
    hello_world = 'hello world'
    successful_response.headers = {
        'content-type': 'text/html'
    }
    successful_response.text = f"""
            <!DOCTYPE html>
            <html>
                <head class="what"></head>
                <body>
                    <div>Hey</div>
                    <div class="container">
                        <h1 id="myid">Title</h1>
                        <a href="{url}"></a>
                        <a href="http://localhost.com"></a>
                        <div>
                            <div>
                                <div>
                                    <h2 class="element">{hello_world}</h2>
                                </div>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
        """
    successful_response.request = crawl_request
    response = successful_response

    assert isinstance(response.html, HtmlParser)
    assert repr(response.html) == 'Node <!DOCTYPE html>'

    el = response.html.find('body')
    assert el[0].tag == 'body'

    els = response.html.find('a')
    assert len(els) == 2
    assert els[0].tag == 'a'
    assert els[0].attr('href') == url

    els = response.html.find('a', first=True)
    assert len(el) == 1
    assert els[0].tag == 'a'

    els = response.html.find('div.container h1#myid')
    assert len(els) == 1
    assert els[0].tag == 'h1'

    els = response.html.find('div.container')
    assert len(els) == 1
    assert els[0].tag == 'div'

    els = response.html.find('.element')
    assert len(els) == 1
    assert els[0].tag == 'h2'
