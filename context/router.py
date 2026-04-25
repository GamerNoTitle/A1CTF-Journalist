from typing import Callable

Handler = Callable[[str], None]


class Router:
    handlers: dict[str, Handler]

    def __init__(self) -> None:
        self.handlers = {}

    def register(self, prefix: str) -> Callable[[Handler], Handler]:
        if prefix in self.handlers:
            raise KeyError
        
        def callback(handler: Handler) -> Handler:
            self.handlers[prefix] = handler
            return handler
        
        return callback
    
    def feed(self, command: str) -> None:
        for prefix, handler in self.handlers.items():
            if command.startswith(prefix):
                params = command[len(prefix):]
                handler(params.strip())
                

router = Router()

@router.register("hello")
def hello(params: str) -> None:
    print(params)
    
router.feed("hello world")
router.feed("nope 111")

