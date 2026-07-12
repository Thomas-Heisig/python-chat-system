TERMINAL_STATUSES = {"completed", "cancelled", "failed", "validation_failed"}
RUNNABLE_STATUSES = {"queued"}
CANCELLABLE_STATUSES = {"queued", "preparing", "running", "evaluating", "saving"}


class TrainingStatus:
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    EVALUATING = "evaluating"
    SAVING = "saving"
    CANCELLING = "cancelling"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    VALIDATION_FAILED = "validation_failed"


def is_terminal(status: str) -> bool:
    return status in TERMINAL_STATUSES
