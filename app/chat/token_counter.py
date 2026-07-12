class TokenCounter:
    def count_text(self, text: str) -> int:
        return max(1, len(text.split()))
