import typer

from libs.llm import LLM, GenerationResult, spinner

from .prompt import prompt

app = typer.Typer(help="Translate text between English and Chinese")


def translate(text: str) -> GenerationResult:
    llm = LLM(prompt)
    return llm.generate_text(text)


@app.command()
def main(
    text: str = typer.Argument(..., help="Text to translate"),
) -> None:
    spinner.text = "Thinking..."
    spinner.start()
    result = translate(text)
    spinner.stop()
    print(result.content)  # newline after streaming output
    print(result.format_footer())


if __name__ == "__main__":
    app()
