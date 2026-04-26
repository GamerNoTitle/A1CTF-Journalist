from typing import Any, Callable, Dict, Union, Coroutine

from a1platform.client import PlatformClient
from napcat.client import NapcatWebsocketServer

Handler = Callable[[str, Dict[str, Any]], Union[str, Coroutine[Any, Any, str], None]]


class Router:
    handlers: dict[str, Handler]

    def __init__(self, platform: PlatformClient, napcat: NapcatWebsocketServer) -> None:
        self.handlers = {}
        self.platform = platform
        self.napcat = napcat

    def register(self, prefix: str) -> Callable[[Handler], Handler]:
        if prefix in self.handlers:
            raise KeyError

        def callback(handler: Handler) -> Handler:
            self.handlers[prefix] = handler
            return handler

        return callback

    async def feed(self, command_line: str, context: Dict[str, Any]) -> str | None:
        text = command_line.strip()
        if not text:
            return None

        parts = text.split(maxsplit=1)
        cmd = parts[0]
        params = parts[1] if len(parts) > 1 else ""

        handler = self.handlers.get(cmd)

        if handler:
            try:
                return await handler(params, context)   # type: ignore
            except Exception as e:
                from utils.logger import log
                import traceback

                traceback.print_exc()
                log(f"[-] Error executing {cmd}: {e}", level="error")
                return f"执行指令出错: {e}"

        return None
