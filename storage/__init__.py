from datetime import datetime
from pydantic import BaseModel

from context.path import get_workdir
from a1platform.models import Notice


class NoticeFileStorage(BaseModel):
    last_updated: datetime = datetime.now()
    notices: list[Notice] = list()

    def append(self, notice: Notice):
        self.notices.append(notice)
        self.last_updated = datetime.now()

    def __repr__(self):
        return f"NoticeFileStorage(notices={self.notices}, last_updated={self.last_updated})"


class NoticeStorage:
    def __init__(self, filename: str):
        self.path = get_workdir() / filename
        self.notices: NoticeFileStorage = NoticeFileStorage()

    def load(self):
        with open(self.path, "r") as f:
            self.notices = NoticeFileStorage.model_validate_json(f.read())

    def save(self):
        with open(self.path, "w") as f:
            f.write(self.notices.model_dump_json(indent=4))

    def is_seen(self, notice_id: int) -> bool:
        return any(notice.notice_id == notice_id for notice in self.notices.notices)

    def __repr__(self):
        return f"NoticeStorage(path={self.path}, notices={self.notices})"


if __name__ == "__main__":
    storage = NoticeStorage("notices.json")
    notice = Notice(
        notice_id=1,
        notice_category="FirstBlood",
        data=["Team A", "Challenge X"],
        create_time="2025-08-15T02:00:16.975239Z",  # type: ignore
        category="Pwn",
    )
    storage.notices.append(notice)
    storage.save()
