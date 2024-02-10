import urllib

import tldextract


class unset:
    """
    Sentinel object singleton to describe a parameter that has not been explicitly set by the user
    """

    def __bool__(self):
        raise Exception(
            "Don't use boolean operators for unset, check identity with 'is', ie: myvar is UNSET")

    def __repr__(self):
        return str(self.__class__)


UNSET = unset()


class Url:
    def __init__(self, url: str):
        self.url = urllib.parse.urlparse(url)
        self.raw_url: str = url

    @property
    def netloc(self):
        return self.url.netloc

    @property
    def domain(self):
        return tldextract.extract(self.raw_url).domain

    def __str__(self):
        return self.url.geturl()

    def __eq__(self, other):
        return self.url.geturl() == other

    def __hash__(self):
        return hash(self.url.geturl())
