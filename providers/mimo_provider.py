"""Xiaomi MiMo API provider."""

from __future__ import annotations
import os
import httpx

from .base import BaseProvider


class MiMoProvider(BaseProvider):
    """Calls MiMo models via OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.mimo.xiaomi.com/v1",
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("MIMO_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def complete(
        self,
        prompt: str,
        model: str = "MiMo-7B-RL",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        resp = self._client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def complete_async(
        self,
        prompt: str,
        model: str = "MiMo-7B-RL",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
