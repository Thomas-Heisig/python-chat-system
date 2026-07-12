from app.chat.token_counter import TokenCounter


def truncate_messages(messages: list[str], max_tokens: int) -> tuple[list[str], int, int]:
    counter = TokenCounter()
    result: list[str] = []
    used = 0
    for item in reversed(messages):
        count = counter.count_text(item)
        if used + count > max_tokens:
            break
        result.append(item)
        used += count
    result.reverse()
    dropped_count = max(0, len(messages) - len(result))
    return result, used, dropped_count
