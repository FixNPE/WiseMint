"""Input safety: prompt injection detection and user distress flagging."""
from __future__ import annotations

import re

_INJECTION_PATTERNS = [
    r"ignore (previous|all|prior|above) instructions",
    r"you are now",
    r"disregard your",
    r"act as (if you are|a|an)",
    r"jailbreak",
    r"pretend (you are|to be)",
    r"bypass (your|the) (safety|filter|guardrail)",
]

_DISTRESS_PATTERNS = [
    r"\b(suicide|kill myself|end my life|self.harm)\b",
    r"\b(hopeless|no reason to live)\b",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)
_DISTRESS_RE = re.compile("|".join(_DISTRESS_PATTERNS), re.IGNORECASE)

DISTRESS_RESPONSE = (
    "I'm not able to help with that, but if you're going through a difficult time, "
    "please reach out to a crisis helpline. In the US: 988 Suicide & Crisis Lifeline (call or text 988)."
)


def check(message: str) -> tuple[bool, str]:
    """Returns (is_safe, reason). If not safe, reason explains why."""
    if _DISTRESS_RE.search(message):
        return False, "distress"
    if _INJECTION_RE.search(message):
        return False, "injection"
    return True, ""
