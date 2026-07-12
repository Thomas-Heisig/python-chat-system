class ChatSystemError(Exception):
    """Base exception for the chat system."""


class ModelLoadError(ChatSystemError):
    pass


class ModelNotAvailableError(ChatSystemError):
    pass


class ModelOutOfMemoryError(ChatSystemError):
    pass


class ContextOverflowError(ChatSystemError):
    pass


class KnowledgeRetrievalError(ChatSystemError):
    pass


class InvalidSettingError(ChatSystemError):
    pass


class BackendUnavailableError(ChatSystemError):
    pass
