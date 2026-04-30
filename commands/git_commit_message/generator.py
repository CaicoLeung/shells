"""Commit message generator using LLM."""

import json
from dataclasses import dataclass
from typing import List

from libs.llm import LLM
from .prompts import (
    COMMIT_MESSAGE_PROMPT,
    BATCH_PLAN_PROMPT,
    BATCH_COMMIT_MESSAGE_PROMPT,
)


@dataclass(frozen=True)
class CommitBatch:
    """A batch of files to commit together."""

    files: List[str]
    reason: str


@dataclass(frozen=True)
class BatchPlan:
    """Plan for committing unstaged changes in batches."""

    batches: List[CommitBatch]


def generate_commit_message(diff: str) -> str:
    """Generate a conventional commit message from a diff."""
    if not diff or not diff.strip():
        return "chore: empty commit"

    llm = LLM(COMMIT_MESSAGE_PROMPT)
    result = llm.generate_text(f"Generate a commit message for this diff:\n\n{diff}")
    return result.content.strip()


def create_batch_plan(diffs: dict[str, str]) -> BatchPlan:
    """Create a plan for committing unstaged changes in batches.

    Args:
        diffs: Dict mapping file paths to their unstaged diffs

    Returns:
        BatchPlan with logical groupings determined by AI
    """
    if not diffs:
        return BatchPlan(batches=[])

    # Build input for LLM
    files_summary = []
    for path, diff in diffs.items():
        # Include truncated diff to avoid huge prompts
        preview = diff[:500] if len(diff) > 500 else diff
        files_summary.append(f"File: {path}\nDiff preview:\n{preview}\n")

    input_text = (
        "Analyze these unstaged changes and group them into logical commits:\n\n"
        + "".join(files_summary)
    )

    llm = LLM(BATCH_PLAN_PROMPT)
    result = llm.generate_text(input_text)

    try:
        # Parse JSON response
        data = json.loads(result.content.strip())
        batches = []
        for batch_data in data.get("batches", []):
            files = batch_data.get("files", [])
            reason = batch_data.get("reason", "Changes")
            # Filter files to only include ones we actually have
            valid_files = [f for f in files if f in diffs]
            if valid_files:
                batches.append(CommitBatch(files=valid_files, reason=reason))
        return BatchPlan(batches=batches)
    except json.JSONDecodeError:
        # Fallback: put all files in one batch
        return BatchPlan(batches=[CommitBatch(files=list(diffs.keys()), reason="All changes")])


def generate_batch_commit_message(reason: str, combined_diff: str) -> str:
    """Generate a commit message for a batch of changes."""
    llm = LLM(BATCH_COMMIT_MESSAGE_PROMPT)
    input_text = f"Batch description: {reason}\n\nCombined diff:\n{combined_diff}"
    result = llm.generate_text(input_text)
    return result.content.strip()
