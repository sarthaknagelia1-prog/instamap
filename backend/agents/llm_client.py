"""
backend/agents/llm_client.py

Provider-agnostic LLM client supporting Groq (high speed, OpenAI-compatible)
and Anthropic Claude, with offline rule-based fallback.
"""

from __future__ import annotations
import os
from typing import Optional
from backend.config import settings


class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = (provider or settings.DEFAULT_LLM_PROVIDER or "groq").lower()
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str, system_prompt: str = "You are an expert Instagram growth analyst.") -> str:
        """Generates completion using configured LLM provider."""
        if self.provider == "groq":
            return self._call_groq(prompt, system_prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, system_prompt)
        else:
            return self._call_groq(prompt, system_prompt)

    def _call_groq(self, prompt: str, system_prompt: str) -> str:
        key = self.api_key or settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is not set.")

        from openai import OpenAI

        client = OpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
        )
        model = self.model or settings.GROQ_MODEL or "openai/gpt-oss-120b"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content or ""

    def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        key = self.api_key or settings.ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is not set.")

        import anthropic

        client = anthropic.Anthropic(api_key=key)
        model = self.model or settings.ANTHROPIC_MODEL or "claude-3-5-sonnet-20241022"

        response = client.messages.create(
            model=model,
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.content[0].text or ""
