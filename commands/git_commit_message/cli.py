"""CLI entry point for git-commit-message command."""

import typer
from halo import Halo

from .git import get_git_status, stage_files, commit_with_message, get_unstaged_diffs, get_staged_diffs, FileChange
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

    # Case 1: We have staged changes - commit them directly
    if status.staged:
        _handle_staged_changes(status.staged, dry_run)
        return

    # Case 2: No staged changes - analyze and batch unstaged
    if status.unstaged:
        _handle_unstaged_changes(status.unstaged, dry_run)
        return

    # Case 3: No changes at all
    typer.echo("No changes to commit.")
    raise typer.Exit(0)


def _handle_staged_changes(staged_changes: list[FileChange], dry_run: bool) -> None:
    """Handle the case where we have staged changes."""
    # Get combined diff of all staged changes
    paths = [c.path for c in staged_changes]

    with Halo(text="Analyzing staged changes...", spinner="dots") as spinner:
        # Get actual staged diffs for the LLM
        diffs = get_staged_diffs(paths)

        # Build combined diff message for LLM
        diff_summary = f"Staged files: {', '.join(paths)}\n\n"
        diff_summary += "Diffs:\n"
        diff_summary += "\n".join(f"--- {path} ---\n{diff}" for path, diff in diffs.items() if diff.strip())

        spinner.stop()
        typer.echo(f"\nFound {len(staged_changes)} staged change(s)")

        if dry_run:
            typer.echo("\nChanges to be committed:")
            for change in staged_changes:
                typer.echo(f"  {change.change_type.value}  {change.path}")
            typer.echo("\n[DRY RUN] Would generate commit message and commit")
            return

        # Generate commit message
        with Halo(text="Generating commit message...", spinner="dots") as msg_spinner:
            message = generate_commit_message(diff_summary)
            msg_spinner.stop()

        typer.echo(f"\nCommit message: {message}")

        # Commit
        with Halo(text="Committing...", spinner="dots") as commit_spinner:
            success = commit_with_message(message)
            commit_spinner.stop()

        if success:
            typer.echo("✓ Changes committed successfully")
        else:
            typer.echo("✗ Commit failed", err=True)
            raise typer.Exit(1)


def _handle_unstaged_changes(unstaged_changes: list[FileChange], dry_run: bool) -> None:
    """Handle the case where we have only unstaged changes."""
    paths = [c.path for c in unstaged_changes]

    with Halo(text="Analyzing unstaged changes...", spinner="dots") as spinner:
        # Get diffs for all unstaged files
        diffs = get_unstaged_diffs(paths)
        spinner.stop()

    if not diffs:
        typer.echo("No diffs found for unstaged files.")
        return

    typer.echo(f"\nFound {len(diffs)} unstaged file(s)")

    # Create batch plan
    with Halo(text="Planning commit batches...", spinner="dots") as spinner:
        plan = create_batch_plan(diffs)
        spinner.stop()

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

    # Stage the files
    with Halo(text="Staging files...", spinner="dots") as spinner:
        success = stage_files(files)
        spinner.stop()

    if not success:
        typer.echo(f"✗ Failed to stage files for batch {batch_num}", err=True)
        return

    # Combine diffs for this batch
    combined_diff = "\n".join(all_diffs[f] for f in files if f in all_diffs)

    # Generate commit message
    with Halo(text="Generating commit message...", spinner="dots") as spinner:
        message = generate_batch_commit_message(reason, combined_diff)
        spinner.stop()

    typer.echo(f"Commit message: {message}")

    # Commit
    with Halo(text="Committing...", spinner="dots") as spinner:
        success = commit_with_message(message)
        spinner.stop()

    if success:
        typer.echo(f"✓ Batch {batch_num} committed successfully")
    else:
        typer.echo(f"✗ Batch {batch_num} commit failed", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
