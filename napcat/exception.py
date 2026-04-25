class NapcatException(Exception): 
    """Base exception for napcat-related errors."""
    def __init__(self, message: str = "An error occurred in the napcat client.")
        super().__init__(message)
        

class SendMsgFailedException(NapcatException): 
    def __init__(self, message: str):
        super().__init__(message)

class ClientIsClosedException(NapcatException): 
    def __init__(self, message: str):
        super().__init__(message)