"""Translate command CLI entry point."""

import typer

from libs.llm import LLM, GenerationResult
from libs.spinner import spinner

from .prompt import prompt

app = typer.Typer(help="Translate text between English and Chinese")


def translate(text: str) -> GenerationResult:
    """Translate text using LLM.

    Args:
        text: The text to translate

    Returns:
        GenerationResult containing the translation
    """
    with LLM(prompt) as llm:
        return llm.generate_text(text)


@app.command()
def main(
    text: str = typer.Argument(..., help="Text to translate"),
) -> None:
    """Translate text between English and Chinese.

    Args:
        text: The text to translate
    """
    with spinner("Thinking..."):
        result = translate(text)

    typer.echo(result.content)  # newline after streaming output
    typer.echo(result.format_footer())


if __name__ == "__main__":
    app()
