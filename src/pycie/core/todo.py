"""Shared helper for student TODO markers."""


def student_todo(task: str) -> None:
    """Raise the canonical TODO exception for unimplemented student logic."""
    raise NotImplementedError(f"TODO(student): {task}")
