import urllib


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
        try:
            self.url = urllib.parse.urlparse(url)
        except Exception as e:
            raise e

        if not self.url.scheme:
            raise Exception(f'Seems that your url {url} is missing the scheme, "http://" or "https://')

    @property
    def netloc(self):
        return self.url.netloc

    def __str__(self):
        return self.url.geturl()

    def __eq__(self, other):
        return self.url.geturl() == other

    def __hash__(self):
        return hash(self.url.geturl())
