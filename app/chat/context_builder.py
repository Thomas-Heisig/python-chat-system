from dataclasses import dataclass

from app.chat.token_budget import TokenBudget
from app.chat.token_counter import TokenCounter
from app.chat.truncation import truncate_messages


@dataclass
class ContextBuildResult:
    prompt: str
    fixed_tokens: int
    used_history_tokens: int
    dropped_history_count: int
    used_knowledge_tokens: int
    dropped_knowledge_count: int


class ContextBuilder:
    def build_with_metrics(
        self,
        system_prompt: str,
        history_messages: list[str],
        user_message: str,
        model_context: int,
        output_reserve: int,
        safety_margin: int = 128,
        knowledge_messages: list[str] | None = None,
    ) -> ContextBuildResult:
        knowledge_items = knowledge_messages or []

        budget = TokenBudget(
            context_limit=model_context,
            output_reserve=output_reserve,
            safety_margin=safety_margin,
        )

        counter = TokenCounter()
        fixed_sections = [
            f"System: {system_prompt}",
            "History:",
            "Knowledge:",
            f"User: {user_message}",
            "Assistant:",
        ]
        fixed_tokens = sum(counter.count_text(section) for section in fixed_sections)
        available_context = max(0, budget.available_context - fixed_tokens)

        trimmed_history, used_history_tokens, dropped_history_count = truncate_messages(history_messages, available_context)
        remaining_for_knowledge = max(0, available_context - used_history_tokens)
        trimmed_knowledge, used_knowledge_tokens, dropped_knowledge_count = truncate_messages(
            knowledge_items,
            remaining_for_knowledge,
        )

        chunks = [
            f"System: {system_prompt}",
            "History:",
            *trimmed_history,
            "Knowledge:",
            *trimmed_knowledge,
            f"User: {user_message}",
            "Assistant:",
        ]

        return ContextBuildResult(
            prompt="\n".join(chunks),
            fixed_tokens=fixed_tokens,
            used_history_tokens=used_history_tokens,
            dropped_history_count=dropped_history_count,
            used_knowledge_tokens=used_knowledge_tokens,
            dropped_knowledge_count=dropped_knowledge_count,
        )

    def build(
        self,
        system_prompt: str,
        history_messages: list[str],
        user_message: str,
        model_context: int,
        output_reserve: int,
        safety_margin: int = 128,
        knowledge_messages: list[str] | None = None,
    ) -> str:
        result = self.build_with_metrics(
            system_prompt=system_prompt,
            history_messages=history_messages,
            user_message=user_message,
            model_context=model_context,
            output_reserve=output_reserve,
            safety_margin=safety_margin,
            knowledge_messages=knowledge_messages,
        )
        return result.prompt
