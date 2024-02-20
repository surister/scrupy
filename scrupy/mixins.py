from scrupy.utils import NOTSET


class HTTPSettingAwareMixin:
    """
    Mixin to inject known attributes from different classes, ie: follow_redirects, headers, user_agent..

    Used to inject attributes from Crawler or Client -> CrawlRequest.
    """
    __http_attrs__ = ('follow_redirects', 'headers', 'user_agent', 'timeout')

    def inject_http_attrs_from(self, other, **override):
        for attr in self.__http_attrs__:
            if attr in override:
                setattr(self, attr, override.get(attr))
                continue

            if getattr(self, attr, NOTSET) is NOTSET:
                setattr(self, attr, getattr(other, attr))
