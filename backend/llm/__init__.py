import os
from typing import Optional
from backend.llm.base import LLMClient, detect_prompt_injection, sanitize_untrusted_input
from backend.llm.gemini_client import GeminiClient
from backend.llm.mock_client import MockLLMClient
from backend.llm.prompts import (
    SYSTEM_SCREENING_INSTRUCTION,
    EXTRACT_JD_PROMPT,
    EXTRACT_RESUME_PROMPT,
    MAP_REQUIREMENTS_PROMPT,
    GENERATE_QUESTION_PROMPT,
    ANALYZE_ANSWER_PROMPT,
    CHECK_CONSISTENCY_PROMPT,
    GENERATE_REPORT_PROMPT,
)
from backend.config import USE_MOCK_LLM, GEMINI_API_KEY


def get_llm_client(
    api_key: Optional[str] = None,
    force_mock: Optional[bool] = None,
) -> LLMClient:
    """
    Factory to obtain the configured LLM client.
    If force_mock is True or USE_MOCK_LLM is True, returns MockLLMClient.
    Otherwise returns GeminiClient (which itself falls back to MockLLMClient if needed).
    """
    if force_mock or (force_mock is None and USE_MOCK_LLM):
        return MockLLMClient()

    key = api_key or GEMINI_API_KEY
    if not key:
        return MockLLMClient()

    return GeminiClient(api_key=key)


__all__ = [
    "LLMClient",
    "GeminiClient",
    "MockLLMClient",
    "get_llm_client",
    "detect_prompt_injection",
    "sanitize_untrusted_input",
    "SYSTEM_SCREENING_INSTRUCTION",
    "EXTRACT_JD_PROMPT",
    "EXTRACT_RESUME_PROMPT",
    "MAP_REQUIREMENTS_PROMPT",
    "GENERATE_QUESTION_PROMPT",
    "ANALYZE_ANSWER_PROMPT",
    "CHECK_CONSISTENCY_PROMPT",
    "GENERATE_REPORT_PROMPT",
]
