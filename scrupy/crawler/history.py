import dataclasses
import datetime
import json
import pathlib

from scrupy import CrawlRequest
from scrupy.request import CrawlResponse


@dataclasses.dataclass
class HistoryRow:
    id: int
    request: CrawlRequest
    response: CrawlResponse
    crawled_at: datetime.datetime

    def as_dict(self):
        obj = dataclasses.asdict(self)
        for k, v in obj.items():
            if hasattr(v, 'as_dict'):
                obj[k] = v.as_dict()
        return obj


class CrawlHistory:
    def __init__(self):
        # Might want to use something more performant in the future, as lookups on runtime in the
        # history might become relevant to avoid repeated crawls, maybe a 'set' which has
        # Operation x in s
        # Average case O(1)
        # Worst Case O(n)
        self.skipped_disallowed = 0
        self.history = []

        self.i = 0

    def add(self, request: CrawlRequest, response: CrawlResponse, crawled_at):
        self.history.append(
            HistoryRow(
                self.i,
                request,
                response,
                crawled_at
            )
        )

        self.i += 1

    def exists(self, url: str):
        """
        Returns whether the given url exists in the history
        """
        for history_row in self.history:
            if history_row.request.url == url:
                return True
        return False

    def save(self, path: str) -> None:
        """
        Persist the history as a Json file in the given `path`

        :param path:
        :return:
        """
        data = [
            row.as_dict() for row in self.history
        ]
        pathlib.Path(path).write_text(json.dumps(data, default=lambda o: str(o)))

    def __getitem__(self, item):
        return self.history[item]

    def __iter__(self):
        return iter(self.history)

    def __str__(self):
        return str(self.history)

    def __len__(self):
        return len(self.history)

    def __repr__(self):
        return self.__str__()
