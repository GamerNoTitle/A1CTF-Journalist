class PlatformException(Exception):
    """Base exception for platform-related errors."""

    def __init__(self, message: str = "An error occurred in the platform client."):
        super().__init__(message)


class CredentialsNotSatisfiedException(PlatformException):
    def __init__(self, message: str):
        super().__init__(message)


class CredentialsNotSetException(PlatformException):
    def __init__(self, message: str):
        super().__init__(message)


class CaptchaFailedToSolveException(PlatformException):
    def __init__(self, message: str):
        super().__init__(message)


class LoginFailedException(PlatformException):
    def __init__(self, message: str):
        super().__init__(message)


class GameNotFoundException(PlatformException):
    def __init__(self, message: str):
        super().__init__(message)


class NoPermissionException(PlatformException):
    def __init__(self, message: str):
        super().__init__(message)


class UnauthorizedAccessException(PlatformException):
    def __init__(self, message: str):
        super().__init__(message)
