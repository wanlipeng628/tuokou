"""Intent router: detect whether user input is natural language or a typo.

Strategy: check for CJK Unified Ideographs. This leverages the fact that
shell commands are purely ASCII — a Chinese user's daily commands never
contain Chinese characters.
"""

import re

# CJK Unified Ideographs + Chinese punctuation
_CJK_PATTERN = re.compile(
    r"[\u4e00-\u9fff"  # CJK Unified Ideographs
    r"\u3400-\u4dbf"   # CJK Extension A
    r"\uf900-\ufaff"   # CJK Compatibility Ideographs
    r"\u3000-\u303f"   # CJK Symbols and Punctuation
    r"\uff00-\uffef"   # Fullwidth Forms
    r"]"
)


def is_natural_language(text: str) -> bool:
    """Check if input is natural language (contains Chinese).

    Args:
        text: Raw user input from the terminal.

    Returns:
        True if Chinese characters are detected, False for pure ASCII.
    """
    return bool(_CJK_PATTERN.search(text))