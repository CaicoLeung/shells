# shells

AI-powered CLI tools for developer workflows.

## Features

- **`git-commit-message`** — Generate Conventional Commits using AI
  - Analyzes staged or unstaged git changes
  - Creates semantic commit batches for unrelated changes
  - Dry-run mode for safe preview
  - Streaming LLM responses with token usage feedback

- **`translate`** — Translate text between English and Chinese
  - Simple command-line translation
  - Streaming output with token statistics

## Installation

### Using uv (recommended)

```bash
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

### Using pipx (isolated installation)

```bash
pipx install .
```

## Configuration

Both commands require an OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."
```

Optional configuration:

```bash
# Custom API base URL (for proxies or compatible services)
export OPENAI_BASE_URL="https://api.openai.com/v1"

# Custom model (defaults to gpt-4o-mini)
export OPENAI_MODEL="gpt-4o-mini"
```

## Global Command Setup

For easier access, install globally and create aliases:

### Using uv tool (recommended)

```bash
# Install as global tool (isolated environment)
uv tool install shells

# Or install from current directory
uv tool install .
```

### Using pipx

```bash
pipx install shells
```

### Aliases (recommended)

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Shorter aliases
alias gcm="git-commit-message"
alias t="translate"
```

Now you can use:
```bash
gcm              # instead of git-commit-message
t "Hello"        # instead of translate "Hello"
```

### Shell completion

Both commands support auto-completion. Enable with:
```bash
# For typer-based completions (zsh/bash)
_git_commit_message_completion() {
    eval $(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=${COMP_CWORD} _GIT_COMMIT_MESSAGE_COMPLETE=complete-bash git-commit-message)
}
complete -F _git_commit_message_completion git-commit-message
```

## Usage

### git-commit-message

Generate conventional commit messages automatically based on your changes.

```bash
# Commit staged changes directly
git-commit-message

# Preview without committing (dry-run)
git-commit-message --dry-run
```

**Behavior:**
- If staged changes exist → analyzes and commits them with an AI-generated message
- If no staged changes → analyzes unstaged changes, creates semantic batches, and commits each batch interactively

The tool automatically groups related files into logical commit batches.

### translate

Translate text between English and Chinese.

```bash
translate "Hello, world!"
# 你好，世界！
```

Output includes token usage statistics:
```
Model: gpt-4o-mini | Input: 12 tokens | Output: 8 tokens | Total: 20 tokens
```

## Development

```bash
# Install with development dependencies
uv sync --group dev

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```

## Project Structure

```
shells/
├── commands/              # CLI entry points
│   ├── git_commit_message/
│   │   ├── cli.py        # Main command interface
│   │   ├── git.py        # Git operations wrapper
│   │   └── generator.py  # LLM commit message generation
│   └── translate/
│       ├── cli.py        # Translation command
│       └── prompt.py     # System prompt for translation
├── libs/                 # Shared utilities
│   └── llm.py            # OpenAI client wrapper with streaming
├── tests/                # pytest tests
└── pyproject.toml        # Project configuration
```

## License

MIT
