"""Output safety: directive scrubbing and educational disclaimer enforcement."""
from __future__ import annotations

import re

DISCLAIMER = (
    "\n\n---\n*This information is for educational purposes only and does not constitute "
    "financial advice. Please consult a licensed financial advisor before making investment decisions.*"
)

_DIRECTIVE_PATTERNS = [
    (r"\byou (must|should|need to|have to) (buy|sell|invest in|purchase)\b", "consider researching"),
    (r"\bimmediately (buy|sell|move)\b", "potentially consider"),
    (r"\bguaranteed (return|profit|gain)\b", "potential return (not guaranteed)"),
]

_DIRECTIVE_RES = [(re.compile(p, re.IGNORECASE), r) for p, r in _DIRECTIVE_PATTERNS]

_ADVICE_TRIGGERS = re.compile(
    r"\b(invest|buy|sell|portfolio|return|profit|loss|stock|bond|fund|allocation)\b",
    re.IGNORECASE,
)


def filter_output(text: str) -> str:
    for pattern, replacement in _DIRECTIVE_RES:
        text = pattern.sub(replacement, text)
    if _ADVICE_TRIGGERS.search(text) and DISCLAIMER not in text:
        text += DISCLAIMER
    return text
