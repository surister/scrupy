from scrupy.utils import UNSET


class HTTPSettingAwareMixin:
    """
    Mixin to inject known attributes from different classes, ie: follow_redirect, headers, user_agent..

    Used to inject attributes from Crawler -> CrawlRequest, respecting priorities.
    """
    __http_attrs__ = ('follow_redirect', 'headers', 'user_agent')

    def inject_http_attrs_from(self, other):
        for attr in self.__http_attrs__:
            if getattr(self, attr, UNSET) is UNSET:
                setattr(self, attr, getattr(other, attr))

        self.headers['User-Agent'] = self.user_agent
