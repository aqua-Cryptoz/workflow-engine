"""Base provider interface for AI model calls."""

from __future__ import annotations
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base for AI providers."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        model: str = "MiMo-7B-RL",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send prompt to model and return text completion."""
        ...

    @abstractmethod
    async def complete_async(
        self,
        prompt: str,
        model: str = "MiMo-7B-RL",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Async version of complete."""
        ...
