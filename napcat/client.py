import json
import random
from typing import Any, Literal
from string import ascii_letters, digits

from fastapi import WebSocket

from napcat.models import GetStatusResponse
from napcat.exception import ClientIsClosedException

COMMANDS = Literal["send_group_msg", "get_status"]

CHARSETS = ascii_letters + digits


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
        resp = await self.connection.receive_json() # type: ignore
        data = GetStatusResponse.model_validate_json(json.dumps(resp))
        return data.status == "ok"

    async def receive_json(self) -> dict[str, Any]:
        if self.connection is None:
            raise ClientIsClosedException("Websocket connection is not established.")
        data = await self.connection.receive_json()
        return data
