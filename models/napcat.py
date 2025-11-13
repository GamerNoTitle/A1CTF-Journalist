from pydantic import BaseModel, Field
from typing import Literal, Any


class SendGroupMsgRespData(BaseModel):
    result: int | None = Field(None)
    errMsg: str | None = Field(None)
    message_id: str | int | None = Field(None)


class SendGroupMsgResponse(BaseModel):
    status: Literal["ok", "error"]
    retcode: int
    data: SendGroupMsgRespData
    message: str
    wording: str
    echo: str


class GetStatusRespData(BaseModel):
    online: bool
    good: bool
    stat: dict[str, Any]


class GetStatusResponse(BaseModel):
    status: Literal["ok", "error"]
    retcode: int
    data: GetStatusRespData
    message: str
    wording: str
    echo: str
