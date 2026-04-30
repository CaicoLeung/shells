"""LLM client wrapper for OpenAI API."""

from collections.abc import Iterable
from dataclasses import dataclass

import openai
from openai.types.chat import ChatCompletionMessageParam

from .config import get_settings

__all__ = ["LLM", "GenerationResult"]


@dataclass
class GenerationResult:
    """LLM generation result with metadata."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def format_footer(self) -> str:
        """Format metadata as a footer."""
        return (
            "\n"
            f"Model: {self.model} | "
            f"Input: {self.prompt_tokens} tokens | "
            f"Output: {self.completion_tokens} tokens | "
            f"Total: {self.total_tokens} tokens"
        )

    def __str__(self) -> str:
        return self.content + self.format_footer()


class LLM:
    """OpenAI LLM client with streaming support."""

    def __init__(self, system_prompt: str) -> None:
        """Initialize the LLM client.

        Args:
            system_prompt: The system prompt to use for all requests
        """
        self._client: openai.OpenAI | None = None
        self.system_prompt = system_prompt
        self._settings = get_settings()

    @property
    def client(self) -> openai.OpenAI:
        """Lazy-initialize the OpenAI client.

        Returns:
            The OpenAI client instance
        """
        if self._client is None:
            self._client = openai.OpenAI(api_key=self._settings.openai_api_key)
        return self._client

    @property
    def model(self) -> str:
        """Get the model name from settings.

        Returns:
            The OpenAI model identifier
        """
        return self._settings.openai_model

    def generate_text(self, prompt: str) -> GenerationResult:
        """Generate text using the LLM.

        Args:
            prompt: The user prompt to send

        Returns:
            GenerationResult containing the generated text and metadata
        """
        messages: Iterable[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        with self.client.chat.completions.stream(
            model=self.model,
            messages=messages,
        ) as stream:
            final = stream.get_final_completion()
            usage = final.usage
            return GenerationResult(
                content=final.choices[0].message.content or "",
                model=final.model,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            )

    def close(self) -> None:
        """Close the OpenAI client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "LLM":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit with cleanup."""
        self.close()
