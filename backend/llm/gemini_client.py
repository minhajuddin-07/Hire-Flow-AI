import os
import json
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError

from backend.llm.base import LLMClient, sanitize_untrusted_input
from backend.llm.mock_client import MockLLMClient
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("hireflow.llm.gemini")
T = TypeVar("T", bound=BaseModel)


class GeminiClient(LLMClient):
    """
    Production client for Google Gemini API via official google-genai SDK.
    Enforces structured Pydantic schema validation, automatic retries with error feedback,
    and automatic graceful fallback if API keys or quotas are unavailable.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = GEMINI_MODEL):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model
        self._client = None
        self._fallback = MockLLMClient()

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as err:
                logger.warning(f"Could not initialize Google GenAI client: {err}. Falling back to mock client.")
                self._client = None

    def call_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """
        Executes Gemini generation with structured response schema and automatic error recovery.
        Falls back safely to local mock parser if connection fails or API key is absent.
        """
        if self._client is None:
            logger.info("Gemini client not initialized; routing call to deterministic fallback engine.")
            return self._fallback.call_structured(prompt, schema, system_instruction)

        from google.genai import types

        config_args = {
            "response_mime_type": "application/json",
            "response_schema": schema,
            "temperature": 0.1,
        }
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_args)
        attempts = 2
        last_error = None

        for attempt in range(1, attempts + 1):
            try:
                curr_prompt = prompt
                if attempt > 1 and last_error:
                    curr_prompt = (
                        f"{prompt}\n\n"
                        f"IMPORTANT: Your previous output failed schema validation with error: {last_error}.\n"
                        f"You MUST return valid JSON adhering strictly to the schema."
                    )

                response = self._client.models.generate_content(
                    model=self.model,
                    contents=curr_prompt,
                    config=config,
                )

                raw_text = response.text
                if not raw_text:
                    raise ValueError("Received empty response from Gemini API.")

                # Validate against schema
                parsed_data = schema.model_validate_json(raw_text)
                return parsed_data

            except (ValidationError, json.JSONDecodeError, ValueError) as err:
                last_error = err
                logger.warning(f"[Gemini attempt {attempt}/{attempts} schema validation issue: {err}]")
                if attempt == attempts:
                    logger.warning("Gemini failed schema validation after retries; engaging fallback engine.")
                    return self._fallback.call_structured(prompt, schema, system_instruction)

            except Exception as err:
                last_error = err
                logger.warning(f"[Gemini attempt {attempt}/{attempts} network/API error: {err}]")
                if attempt == attempts:
                    logger.warning(f"Gemini API error ({err}); engaging fallback engine.")
                    return self._fallback.call_structured(prompt, schema, system_instruction)

        return self._fallback.call_structured(prompt, schema, system_instruction)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generates raw text from Gemini with fallback."""
        if self._client is None:
            return self._fallback.generate_text(prompt, system_instruction)

        try:
            from google.genai import types
            config_args = {"temperature": 0.2}
            if system_instruction:
                config_args["system_instruction"] = system_instruction
            config = types.GenerateContentConfig(**config_args)

            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as err:
            logger.warning(f"Gemini text generation failed: {err}. Using fallback.")
            return self._fallback.generate_text(prompt, system_instruction)
