import re

_SALUTATION_PATTERN = re.compile(
    r"^\s*(?:"
    r"亲爱的(?:过去的你|未来的我|未来的你|过去的我)\s*[：:,，]?"
    r"|dear\s+(?:past\s+you|future\s+you|future\s+me|past\s+me|past\s+self|future\s+self)\s*[,：:]?"
    r")\s*",
    re.IGNORECASE,
)


def clean_letter_body(letter: str) -> str:
    """Keep the greeting in the UI/email, so stored model output is body-only."""

    body = letter.strip()
    previous = None
    while body and body != previous:
        previous = body
        body = _SALUTATION_PATTERN.sub("", body, count=1).lstrip()
    return body


def is_chinese_text(text: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in text)
