from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class Notice(BaseModel):
    created_at: datetime = Field(..., alias="create_time")
    data: list[str]
    notice_category: Literal[
        "FirstBlood", "SecondBlood", "ThirdBlood", "NewAnnouncement", "NewHint"
    ]
    notice_id: int

    def __str__(self) -> str:
        match self.notice_category:
            case "FirstBlood":
                return f"🥇 队伍「{self.data[0]}」斩获了题目「{self.data[1]}」的第一滴血！\nTime: {self.created_at.now():%Y-%m-%d %H:%M:%S}"
            case "SecondBlood":
                return f"🥈 队伍「{self.data[0]}」获得了题目「{self.data[1]}」的第二滴血！\nTime: {self.created_at.now():%Y-%m-%d %H:%M:%S}"
            case "ThirdBlood":
                return f"🥉 队伍「{self.data[0]}」获得了题目「{self.data[1]}」的第三滴血！\nTime: {self.created_at.now():%Y-%m-%d %H:%M:%S}"
            case "NewAnnouncement":
                return f"📢 新公告发布：\n标题: {'\n'.join(self.data)}\nTime: {self.created_at.now():%Y-%m-%d %H:%M:%S}"
            case "NewHint":
                return f"💡 题目「{self.data[0]}」发布了新提示，请前往平台查看\nTime: {self.created_at.now():%Y-%m-%d %H:%M:%S}"

    def __repr__(self) -> str:
        return f"Notice(notice_id={self.notice_id}, notice_category={self.notice_category}, created_at={self.created_at}, data={self.data})"

class NoticeResponse(BaseModel):
    code: int
    data: list[Notice]
