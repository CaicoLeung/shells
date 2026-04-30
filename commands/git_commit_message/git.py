"""Git operations module for commit message generation.

This module provides a wrapper around git commands using subprocess,
supporting status checking, staging, and committing operations.
"""

import subprocess
from dataclasses import dataclass
from enum import Enum


class ChangeType(Enum):
    """Enumeration of git file change types.

    Values correspond to git status codes:
    - A: Added
    - M: Modified
    - D: Deleted
    - R: Renamed
    - C: Copied
    """
    ADDED = 'A'
    MODIFIED = 'M'
    DELETED = 'D'
    RENAMED = 'R'
    COPIED = 'C'


@dataclass(frozen=True)
class FileChange:
    """Represents a single file change in git."""
    path: str
    change_type: ChangeType
    is_staged: bool


@dataclass(frozen=True)
class GitStatus:
    """Represents the current git status."""
    staged: list[FileChange]
    unstaged: list[FileChange]


def _run_git_command(args: list[str]) -> str:
    """Run a git command via subprocess and return stdout.

    Args:
        args: List of command-line arguments to pass to git

    Returns:
        The stdout output from the git command as a string

    Raises:
        RuntimeError: If git reports it's not a repository
    """
    result = subprocess.run(
        ['git'] + args,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0 and 'not a git repository' in result.stderr.lower():
        raise RuntimeError("Not a git repository")
    return result.stdout.strip()


def _parse_git_status_output(output: str, is_staged: bool) -> list[FileChange]:
    """Parse git diff --name-status output into FileChange objects.

    Git output format is typically:
    - Single status code: "M\\tpath/to/file"
    - Combined status codes: "AM\\tpath/to/file" (added, then modified)

    Args:
        output: The raw output from git diff --name-status
        is_staged: Whether these changes are staged

    Returns:
        List of FileChange objects parsed from the output
    """
    if not output.strip():
        return []

    changes: list[FileChange] = []

    for line in output.strip().split('\n'):
        if not line:
            continue

        # Split on tab to separate status code(s) from path
        parts = line.split('\t')
        if len(parts) < 2:
            continue

        status_code = parts[0]
        path = parts[1]

        # Handle combined status codes like "AM" - check last character
        last_char = status_code[-1]

        try:
            change_type = ChangeType(last_char)
        except ValueError:
            # If not a valid single-character code, skip this entry
            continue

        changes.append(FileChange(
            path=path,
            change_type=change_type,
            is_staged=is_staged
        ))

    return changes


def get_git_status() -> GitStatus:
    """Get both staged and unstaged changes from git.

    Returns:
        GitStatus object containing staged and unstaged file changes
    """
    # Get staged changes
    staged_output = _run_git_command(['diff', '--staged', '--name-status'])
    staged = _parse_git_status_output(staged_output, is_staged=True)

    # Get unstaged changes (modified tracked files)
    unstaged_output = _run_git_command(['diff', '--name-status'])
    unstaged = _parse_git_status_output(unstaged_output, is_staged=False)

    # Get untracked files (new files not yet staged)
    untracked_output = _run_git_command(['ls-files', '--others', '--exclude-standard'])
    untracked = [
        FileChange(path=path.strip(), change_type=ChangeType.ADDED, is_staged=False)
        for path in untracked_output.strip().split('\n')
        if path.strip()
    ]

    # Merge unstaged tracked changes with untracked files
    unstaged.extend(untracked)

    return GitStatus(staged=staged, unstaged=unstaged)


def stage_files(file_paths: list[str]) -> bool:
    """Stage files via git add.

    Args:
        file_paths: List of file paths to stage

    Returns:
        True if successful, False otherwise
    """
    if not file_paths:
        return False

    result = subprocess.run(
        ['git', 'add'] + file_paths,
        capture_output=True,
        text=True,
        check=False
    )

    return result.returncode == 0


def get_file_diff(file_path: str, staged: bool = False) -> str:
    """Get diff for a single file.

    Args:
        file_path: Path to the file to get diff for
        staged: If True, get staged diff; otherwise get unstaged diff

    Returns:
        The diff output as a string, or empty string if no diff
    """
    args = ['diff']
    if staged:
        args.append('--staged')
    args.extend(['--', file_path])

    return _run_git_command(args)


def get_diffs(file_paths: list[str], staged: bool = False) -> dict[str, str]:
    """Get diffs for multiple files in a single git command.

    Args:
        file_paths: List of file paths to get diffs for
        staged: If True, get staged diffs; otherwise get unstaged diffs

    Returns:
        Dictionary mapping file paths to their diff strings
    """
    if not file_paths:
        return {}

    args = ['diff']
    if staged:
        args.append('--staged')
    args.extend(['--'] + file_paths)

    output = _run_git_command(args)
    return _parse_multi_file_diff(output)


def _parse_multi_file_diff(output: str) -> dict[str, str]:
    """Parse multi-file diff output into a dictionary.

    Git diff output format uses file headers like:
    diff --git a/path/to/file b/path/to/file
    """
    if not output:
        return {}

    diffs: dict[str, str] = {}
    current_file: str | None = None
    current_diff_lines: list[str] = []

    for line in output.split('\n'):
        if line.startswith('diff --git '):
            if current_file:
                diffs[current_file] = '\n'.join(current_diff_lines).rstrip()

            parts = line.split()
            if len(parts) >= 3:
                current_file = parts[2][2:] if parts[2].startswith('a/') else parts[2]
                current_diff_lines = []
        elif current_file is not None:
            current_diff_lines.append(line)

    if current_file:
        diffs[current_file] = '\n'.join(current_diff_lines).rstrip()

    return diffs


def commit_with_message(message: str) -> bool:
    """Commit staged changes with the given message.

    Args:
        message: The commit message to use

    Returns:
        True if successful, False otherwise
    """
    if not message:
        return False

    result = subprocess.run(
        ['git', 'commit', '-m', message],
        capture_output=True,
        text=True,
        check=False
    )

    return result.returncode == 0
