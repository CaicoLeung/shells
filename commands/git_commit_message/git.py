"""Git operations module for commit message generation.

This module provides a wrapper around git commands using subprocess,
supporting status checking, staging, and committing operations.
"""

import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List


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
    """Represents a single file change in git.

    Attributes:
        path: The file path relative to git root
        change_type: The type of change (added, modified, deleted, etc.)
        is_staged: Whether the change is staged for commit
    """
    path: str
    change_type: ChangeType
    is_staged: bool


@dataclass(frozen=True)
class GitStatus:
    """Represents the current git status.

    Attributes:
        staged: List of staged file changes
        unstaged: List of unstaged file changes
    """
    staged: List[FileChange]
    unstaged: List[FileChange]


def _run_git_command(args: List[str]) -> str:
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


def _parse_git_status_output(output: str, is_staged: bool) -> List[FileChange]:
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

    changes: List[FileChange] = []

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


def stage_files(file_paths: List[str]) -> bool:
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


def get_unstaged_diffs(file_paths: List[str]) -> dict[str, str]:
    """Get diffs for multiple unstaged files.

    Args:
        file_paths: List of file paths to get diffs for

    Returns:
        Dictionary mapping file paths to their diff strings
    """
    diffs = {}

    for file_path in file_paths:
        diff = get_file_diff(file_path, staged=False)
        diffs[file_path] = diff

    return diffs


def get_staged_diffs(file_paths: List[str]) -> dict[str, str]:
    """Get diffs for multiple staged files.

    Args:
        file_paths: List of file paths to get diffs for

    Returns:
        Dictionary mapping file paths to their staged diff strings
    """
    diffs = {}

    for file_path in file_paths:
        diff = get_file_diff(file_path, staged=True)
        diffs[file_path] = diff

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
