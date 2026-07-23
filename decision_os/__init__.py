"""Repository-local Decision-OS reference tools."""

from .checks import EXIT_CONTRADICTION, EXIT_INCOMPLETE, EXIT_NOT_GIT, inspect_repository

__all__ = [
    "EXIT_CONTRADICTION",
    "EXIT_INCOMPLETE",
    "EXIT_NOT_GIT",
    "inspect_repository",
]
