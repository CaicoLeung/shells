import os
from collections.abc import Iterable
from dataclasses import dataclass

import openai
from halo import Halo
from openai.types.chat import ChatCompletionMessageParam


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
    def __init__(self, system_prompt: str) -> None:
        self.client = openai.OpenAI()
        self.system_prompt = system_prompt

    def generate_text(self, prompt: str) -> GenerationResult:
        model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

        messages: Iterable[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        with self.client.chat.completions.stream(
            model=model,
            messages=messages,
        ) as stream:
            for event in stream:
                if event.type == "content.delta":
                    print(event.delta, end="", flush=True)

        final = stream.get_final_completion()
        usage = final.usage
        return GenerationResult(
            content=final.choices[0].message.content or "",
            model=final.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )
