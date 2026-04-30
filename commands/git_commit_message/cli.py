"""CLI entry point for git-commit-message command."""

import typer
from halo import Halo

from .git import get_git_status, stage_files, commit_with_message, get_diffs, FileChange
from .generator import generate_commit_message, create_batch_plan, generate_batch_commit_message, CommitBatch

app = typer.Typer(help="Generate Conventional Commits using AI")


@app.command()
def main(
    dry_run: bool = typer.Option(False, '--dry-run', '-n', help='Show what would be committed without committing'),
) -> None:
    """Generate and commit changes with AI-generated commit messages.

    If staged changes exist: commits them directly.
    If no staged changes: analyzes unstaged changes and commits in batches.
    """
    spinner = Halo(text="Checking git status...", spinner="dots")
    spinner.start()

    try:
        status = get_git_status()
    except RuntimeError as e:
        spinner.stop()
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    spinner.stop()

    if status.staged:
        _handle_staged_changes(status.staged, dry_run)
        return

    if status.unstaged:
        _handle_unstaged_changes(status.unstaged, dry_run)
        return

    typer.echo("No changes to commit.")
    raise typer.Exit(0)


def _handle_staged_changes(staged_changes: list[FileChange], dry_run: bool) -> None:
    paths = [c.path for c in staged_changes]

    with Halo(text="Analyzing staged changes...", spinner="dots"):
        diffs = get_diffs(paths, staged=True)

        diff_summary = f"Staged files: {', '.join(paths)}\n\n"
        diff_summary += "Diffs:\n"
        diff_summary += "\n".join(f"--- {path} ---\n{diff}" for path, diff in diffs.items() if diff.strip())

    typer.echo(f"\nFound {len(staged_changes)} staged change(s)")

    if dry_run:
        typer.echo("\nChanges to be committed:")
        for change in staged_changes:
            typer.echo(f"  {change.change_type.value}  {change.path}")
        typer.echo("\n[DRY RUN] Would generate commit message and commit")
        return

    with Halo(text="Generating commit message...", spinner="dots"):
        message = generate_commit_message(diff_summary)

    typer.echo(f"\nCommit message: {message}")

    with Halo(text="Committing...", spinner="dots"):
        success = commit_with_message(message)

    if success:
        typer.echo("✓ Changes committed successfully")
    else:
        typer.echo("✗ Commit failed", err=True)
        raise typer.Exit(1)


def _handle_unstaged_changes(unstaged_changes: list[FileChange], dry_run: bool) -> None:
    paths = [c.path for c in unstaged_changes]

    with Halo(text="Analyzing unstaged changes...", spinner="dots"):
        diffs = get_diffs(paths, staged=False)

    if not diffs:
        typer.echo("No diffs found for unstaged files.")
        return

    typer.echo(f"\nFound {len(diffs)} unstaged file(s)")

    with Halo(text="Planning commit batches...", spinner="dots"):
        plan = create_batch_plan(diffs)

    typer.echo(f"Created {len(plan.batches)} batch(es)")

    for i, batch in enumerate(plan.batches, 1):
        _process_batch(i, batch, diffs, dry_run)


def _process_batch(
    batch_num: int,
    batch: CommitBatch,
    all_diffs: dict[str, str],
    dry_run: bool
) -> None:
    """Process a single batch of changes."""
    files, reason = batch.files, batch.reason

    typer.echo(f"\n--- Batch {batch_num}: {reason} ---")
    typer.echo(f"Files: {', '.join(files)}")

    if dry_run:
        typer.echo("[DRY RUN] Would stage, generate message, and commit")
        return

    with Halo(text="Staging files...", spinner="dots"):
        success = stage_files(files)

    if not success:
        typer.echo(f"✗ Failed to stage files for batch {batch_num}", err=True)
        return

    combined_diff = "\n".join(all_diffs[f] for f in files if f in all_diffs)

    with Halo(text="Generating commit message...", spinner="dots"):
        message = generate_batch_commit_message(reason, combined_diff)

    typer.echo(f"Commit message: {message}")

    with Halo(text="Committing...", spinner="dots"):
        success = commit_with_message(message)

    if success:
        typer.echo(f"✓ Batch {batch_num} committed successfully")
    else:
        typer.echo(f"✗ Batch {batch_num} commit failed", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
