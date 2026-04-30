"""Tests for git-commit-message CLI."""

import pytest
from typer.testing import CliRunner
from commands.git_commit_message.cli import app

runner = CliRunner()


def test_cli_exists():
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'generate and commit changes' in result.stdout.lower()


def test_cli_main_command_exists():
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
