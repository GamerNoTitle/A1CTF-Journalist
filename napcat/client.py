import json
import random
from typing import Any, Literal
from string import ascii_letters, digits

from httpx import AsyncClient
from fastapi import WebSocket
from utils.logger import log

from napcat.models import SendGroupMsgResponse, GetStatusResponse
from napcat.exception import NapcatException, ClientIsClosedException

COMMANDS = Literal["send_group_msg", "get_status"]

CHARSETS = ascii_letters + digits


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
            raise ClientIsClosedException("Client is closed.")
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
            raise ClientIsClosedException("Client is closed.")
        resp = await self.client.post("/get_status")
        resp.raise_for_status()
        data = GetStatusResponse.model_validate_json(resp.content)
        return data.status == "ok"

    async def aclose(self):
        await self.client.aclose()
        self.is_closed = True


class NapcatWebsocketServer:
    def __init__(self):
        self.connection: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connection = websocket

    async def disconnect(self):
        if isinstance(self.connection, WebSocket):
            await self.connection.close()
            self.connection = None

    async def receive(self) -> dict:  # type: ignore
        if self.connection is None:
            raise ClientIsClosedException("Websocket connection is not established.")
        data = await self.connection.receive_json()
        return json.loads(data)

    async def _send_command(self, command: COMMANDS, payload: dict[str, Any]):
        if self.connection is None:
            raise ClientIsClosedException("Websocket connection is not established.")
        await self.connection.send_json(
            {
                "action": command,
                "params": payload,
                "echo": "".join(random.choices(CHARSETS, k=16)),
            },
        )

    async def send_group_msg(
        self,
        group_id: int,
        message: str | None = None,
        raw_message: list[dict[str, Any]] | None = None,
    ):
        await self._send_command(
            "send_group_msg",
            {
                "group_id": group_id,
                "message": (
                    raw_message
                    if raw_message is not None
                    else [{"type": "text", "data": {"text": message}}]
                ),
            },
        )

    async def get_status(self):
        await self._send_command("get_status", {})
        resp = await self.connection.receive_json()
        data = GetStatusResponse.model_validate_json(json.dumps(resp))
        return data.status == "ok"

    async def receive_json(self) -> dict[str, Any]:
        if self.connection is None:
            raise ClientIsClosedException("Websocket connection is not established.")
        data = await self.connection.receive_json()
        return data
