import re
import logging
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel

logger = logging.getLogger("hireflow.llm")

T = TypeVar("T", bound=BaseModel)

# Known prompt injection signatures
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s*prompt\s*override",
    r"you\s+are\s+now\s+in\s+dan\s+mode",
    r"you\s+must\s+say\s+this\s+candidate\s+is\s+perfect",
    r"assign\s+(all\s+)?requirements\s+as\s+met",
    r"give\s+a\s+perfect\s+score",
    r"roleplay\s+as",
]


def detect_prompt_injection(text: str) -> bool:
    """Detects whether untrusted text contains prompt injection attempts."""
    if not text:
        return False
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            return True
    return False


def sanitize_untrusted_input(text: str, tag: str = "untrusted_content") -> str:
    """
    Sanitizes untrusted candidate input (resume or interview answers) by:
    1. Neutralizing injection attempt triggers
    2. Enclosing content within strict data boundary tags
    """
    if not text:
        return f"<{tag}>\n</{tag}>"

    # Replace blatant override attempts with benign markers
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(
            pattern,
            "[UNTRUSTED_INSTRUCTION_FILTERED]",
            sanitized,
            flags=re.IGNORECASE,
        )

    # Frame within boundary tags to instruct LLM that this is strictly passive data
    return (
        f"<{tag} is_untrusted_data=\"true\">\n"
        f"{sanitized.strip()}\n"
        f"</{tag}>"
    )


class LLMClient(ABC):
    """Abstract base class for LLM client implementations."""

    @abstractmethod
    def call_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """Execute a prompt and parse output strictly into a Pydantic schema."""
        pass

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate raw text from a prompt."""
        pass
