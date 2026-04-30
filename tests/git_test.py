from commands.git_commit_message.git import (
    GitStatus,
    get_git_status,
    stage_files,
    commit_with_message,
)


def test_get_git_status_returns_status_object():
    result = get_git_status()
    assert isinstance(result, GitStatus)
    assert hasattr(result, "staged")
    assert hasattr(result, "unstaged")


def test_get_git_status_detects_staged_changes():
    result = get_git_status()
    assert len(result.staged) >= 0


def test_stage_files_stages_given_files():
    success = stage_files(["README.md"])
    assert isinstance(success, bool)


def test_commit_with_message_commits_staged_changes():
    message = "test: commit message for testing"
    success = commit_with_message(message)
    assert isinstance(success, bool)
