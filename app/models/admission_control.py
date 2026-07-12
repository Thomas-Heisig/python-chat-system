import psutil
from dataclasses import dataclass
from app.core.config import get_config


@dataclass
class AdmissionDecision:
    accepted: bool
    reason: str | None = None


class AdmissionControl:
    def __init__(self) -> None:
        self.config = get_config()

    def evaluate(self, active_generations: int, queue_length: int) -> AdmissionDecision:
        if active_generations >= self.config.max_active_generations:
            return AdmissionDecision(False, "too_many_active_generations")
        if queue_length >= self.config.max_queue_length:
            return AdmissionDecision(False, "queue_limit_reached")

        vm = psutil.virtual_memory()
        used_mb = int((vm.total - vm.available) / (1024 * 1024))
        if used_mb > self.config.ram_memory_limit_mb:
            return AdmissionDecision(False, "ram_limit_reached")

        return AdmissionDecision(True, None)
