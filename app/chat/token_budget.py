from dataclasses import dataclass


@dataclass
class TokenBudget:
    context_limit: int
    output_reserve: int
    safety_margin: int

    @property
    def available_context(self) -> int:
        return max(0, self.context_limit - self.output_reserve - self.safety_margin)
