import inspect
from typing import Any, Callable, Dict, Union, Awaitable

from a1platform.client import PlatformClient
from napcat.client import NapcatWebsocketServer

HandlerReturn = Union[str, None]
Handler = Callable[
    [str, Dict[str, Any]], Union[HandlerReturn, Awaitable[HandlerReturn]]
]


class Router:
    handlers: dict[str, Handler]

    def __init__(
        self, platform: PlatformClient, napcat: NapcatWebsocketServer, *prefixes: str
    ) -> None:
        self.handlers = {}
        self.platform = platform
        self.napcat = napcat
        self.prefixes = prefixes

    def register(self, *command: str) -> Callable[[Handler], Handler]:
        for cmd in command:
            if cmd in self.handlers:
                raise KeyError

        def callback(handler: Handler) -> Handler:
            for cmd in command:
                self.handlers[cmd] = handler
            return handler

        return callback

    async def feed(self, command_line: str, context: Dict[str, Any]) -> str | None:
        text = command_line.strip()
        if not text:
            return None
        hit_prefix = ""
        for prefix in self.prefixes:
            if text.startswith(prefix):
                hit_prefix = prefix
                break
        if not hit_prefix:
            return None
        parts = text.split(maxsplit=1)
        cmd = parts[0].removeprefix(hit_prefix)
        params = parts[1] if len(parts) > 1 else ""

        handler = self.handlers.get(cmd)

        if handler:
            try:
                result = handler(params, context)
                if inspect.isawaitable(result):
                    return await result
                else:
                    return result
            except Exception as e:
                from utils.logger import log
                import traceback

                traceback.print_exc()
                log(f"[-] Error executing {cmd}: {e}", level="error")
                return f"执行指令出错: {e}"

        return None
