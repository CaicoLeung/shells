import pytest
from commands.git_commit_message.generator import (
    generate_commit_message,
    BatchPlan,
    create_batch_plan,
)
from commands.git_commit_message.git import FileChange, ChangeType


def test_generate_commit_message_returns_conventional_format():
    diff = "diff --git a/test.py b/test.py\n+ def new_function():\n+     pass"
    result = generate_commit_message(diff)
    assert isinstance(result, str)
    # Should follow conventional commits: type(scope): description
    assert any(
        result.startswith(t)
        for t in ["feat:", "fix:", "chore:", "docs:", "refactor:", "test:", "style:"]
    )


def test_generate_commit_message_for_feature_addition():
    diff = "diff --git a/test.py b/test.py\n+ def authenticate_user():\n+     return True"
    result = generate_commit_message(diff)
    assert result is not None
    assert len(result) > 0


def test_create_batch_plan_for_unstaged_changes():
    diffs = {
        "auth/login.py": "+ def login(): pass",
        "auth/logout.py": "+ def logout(): pass",
        "ui/button.py": "+ class Button: pass",
    }
    result = create_batch_plan(diffs)
    assert isinstance(result, BatchPlan)
    assert len(result.batches) > 0
    # Each batch should have files and a reason
    for batch in result.batches:
        assert len(batch.files) > 0
        assert len(batch.reason) > 0


def test_create_batch_plan_empty_diffs():
    result = create_batch_plan({})
    assert isinstance(result, BatchPlan)
    assert len(result.batches) == 0


def test_generate_commit_message_empty_diff():
    result = generate_commit_message("")
    assert result == "chore: empty commit"
