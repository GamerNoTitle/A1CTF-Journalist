class RouterException(Exception):
    """Base class for exceptions in the router."""

    def __init__(self, message: str):
        super().__init__(message)


class RouterParseException(RouterException):
    """Exception raised for errors in parsing commands."""

    def __init__(self, message: str):
        super().__init__(message)
