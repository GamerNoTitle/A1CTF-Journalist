import json
from typing import Any

from httpx import AsyncClient
from utils.logger import log

from napcat.models import SendGroupMsgResponse, GetStatusResponse
from napcat.exception import NapcatException, ClientIsClosedException


class NapcatClient:
    def __init__(self, base_url: str, token: str):
        self.client = AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
        self.is_closed = False

    async def send_group_msg(self, group_id: str, message: str) -> None:
        """
        发送单条群消息
        :param group_id: 目标群号
        :param message: 消息内容，支持多条消息合并发送
        """
        if self.is_closed:
            raise ClientIsClosedException
        payload: dict[str, Any] = {
            "group_id": group_id,
            "message": [{"type": "text", "data": {"text": message}}],
        }
        resp = await self.client.post("/send_group_msg", json=payload)
        resp.raise_for_status()
        log(json.dumps(resp.json(), ensure_ascii=False))
        data = SendGroupMsgResponse.model_validate_json(resp.content)
        if data.status != "ok":
            raise NapcatException()

    async def check_alive(self) -> bool:
        """
        检查 Napcat 服务是否存活
        :return bool: 服务存活状态
        """
        if self.is_closed:
            raise ClientIsClosedException
        resp = await self.client.post("/get_stats")
        resp.raise_for_status()
        data = GetStatusResponse.model_validate_json(resp.content)
        return data.status == "ok"

    async def aclose(self):
        await self.client.aclose()
        self.is_closed = True
