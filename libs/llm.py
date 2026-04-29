import os
import openai
from dataclasses import dataclass
from halo import Halo


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

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        spinner = Halo(text="Thinking...", spinner="dots")
        spinner.start()
        first_chunk = True

        try:
            with self.client.chat.completions.stream(
                model=model,
                messages=messages,
            ) as stream:
                for event in stream:
                    if event.type == 'content.delta':
                        if first_chunk:
                            spinner.stop()
                            first_chunk = False
                        print(event.delta, end="", flush=True)
        finally:
            # Ensure spinner is stopped even if no content was received
            if not first_chunk:
                spinner.clear()  # Clear the spinner line if content was printed
            else:
                spinner.stop()

        final = stream.get_final_completion()
        return GenerationResult(
            content=final.choices[0].message.content or "",
            model=final.model,
            prompt_tokens=final.usage.prompt_tokens,
            completion_tokens=final.usage.completion_tokens,
            total_tokens=final.usage.total_tokens,
        )
