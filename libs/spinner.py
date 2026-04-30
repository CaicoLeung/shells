"""Centralized spinner management using rich."""

from contextlib import contextmanager
from rich.console import Console
from rich.status import Status

console = Console()


@contextmanager
def spinner(text: str):
    """Context manager for spinner with automatic start/stop.

    Args:
        text: The status text to display

    Yields:
        None
    """
    with console.status(f"[bold green]{text}") as status:
        yield status


__all__ = ["spinner", "console"]
