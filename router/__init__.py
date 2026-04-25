import asyncio
from typing import Any, Callable, Dict, Union, Coroutine

from a1platform.client import PlatformClient
from napcat.client import NapcatWebsocketServer
from router.exception import RouterException

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
    
    async def feed(self, command: str, context: Dict[str, Any]) -> None:
        for prefix, handler in self.handlers.items():
            if command.startswith(prefix):
                params = command[len(prefix):]
            try:
                response = handler(params, context)

                if asyncio.iscoroutine(response):   # 如果是协程
                    result = await response
                else:
                    result = response

                if isinstance(result, str):
                    return result   # 返回对应的字符串结果
                elif result is None:
                    return None
                else:
                    raise RouterException(f"Handler for prefix '{prefix}' returned an unsupported type: {type(result)}")
            
            except Exception as e:
                raise RouterException(f"处理命令时发生错误: {e}")
        
        return None                

# router = Router()

# @router.register("!!rank")
# def get_rank(params: str):
#     ...
    
# @router.register("!!challenge")
# def get_challenge_info(params: str):
#     ...
    
# @router.register("!!team")
# def get_team(params: str):
#     ...
    

    
# @router.register("!!test")
# def get_test(params: str):
#     print(f"Received test command with params: {params}")

# router.feed("!!test Hello 1 2 3 4 5")

