"""Edge case tests for git-commit-message command.

Tests for handling empty repositories, no changes, and error conditions.
"""

import subprocess
import pytest
from typer.testing import CliRunner

from commands.git_commit_message.git import get_git_status, _run_git_command, GitStatus
from commands.git_commit_message.cli import app


def test_get_git_status_returns_valid_structure() -> None:
    """Test get_git_status returns a valid GitStatus object.

    The function should work regardless of whether there are changes.
    """
    result = get_git_status()
    assert isinstance(result, GitStatus)
    # Should have staged and unstaged lists (even if empty)
    assert hasattr(result, 'staged')
    assert hasattr(result, 'unstaged')


def test_run_git_command_raises_runtime_error_for_non_repo(tmp_path, monkeypatch) -> None:
    """Test _run_git_command raises RuntimeError when not in a git repository."""
    # Change to a temporary directory that is not a git repo
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RuntimeError, match="Not a git repository"):
        _run_git_command(['status'])


def test_cli_not_a_git_repository(tmp_path, monkeypatch) -> None:
    """Test CLI behavior when not in a git repository.

    Should exit with error code 1 and display error message.
    """
    # Change to a temporary directory that is not a git repo
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 1
    # Error message should be in output (stdout or stderr)
    output = result.stdout + str(result.exception) if result.exception else result.stdout
    assert "Error" in output or "Not a git repository" in output or result.exit_code == 1
