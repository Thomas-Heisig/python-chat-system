from app.models.backends.base import ModelBackend


def check_backend_health(backend: ModelBackend | None) -> bool:
    if backend is None:
        return False
    return backend.health_check()
