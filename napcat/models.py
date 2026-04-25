from pydantic import BaseModel
from typing import Literal, Any


class SendGroupMsgRespData(BaseModel):
    # result: int | None = Field(None)
    # errMsg: str | None = Field(None)
    message_id: int | None = None
    res_id: str | None = None
    forward_id: str | None = None


class SendGroupMsgResponse(BaseModel):
    status: Literal["ok", "error"]
    retcode: int
    data: SendGroupMsgRespData
    message: str
    wording: str
    echo: str | None = None


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
