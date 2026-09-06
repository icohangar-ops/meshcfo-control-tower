"""Nebius Token Factory client for NVIDIA Nemotron open models."""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from meshcfo_control_tower.config import Settings

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class TokenFactoryError(RuntimeError):
    pass


class TokenFactoryClient:
    """OpenAI-compatible chat client pointed at Token Factory."""

    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.live_llm_ready:
            raise TokenFactoryError(
                "NEBIUS_API_KEY is not set. Export it or use --offline."
            )
        self._client = OpenAI(
            base_url=settings.nebius_base_url,
            api_key=settings.nebius_api_key,
        )
        self.model_used = settings.nebius_model
        self.used_fallback = False

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for model, is_fallback in (
            (self.settings.nebius_model, False),
            (self.settings.nebius_fallback_model, True),
        ):
            if not model:
                continue
            try:
                payload = self._call(
                    model=model,
                    system=system,
                    user=user,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                self.model_used = model
                self.used_fallback = is_fallback
                return payload
            except Exception as exc:  # noqa: BLE001 — try fallback model
                last_error = exc
                continue
        raise TokenFactoryError(
            f"Token Factory call failed for Nemotron models: {last_error}"
        )

    def _call(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        # Nemotron 3 Nano may emit a reasoning trace; disable thinking when the
        # serving stack honors chat_template_kwargs, and always strip traces.
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        system
                        + " /no_think Return a single JSON object only. "
                        + "Do not invent real-company facts. "
                        + "Ground every claim in the provided DEMO excerpts."
                    ),
                },
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            response = self._client.chat.completions.create(
                **kwargs,
                response_format={"type": "json_object"},
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
        except Exception:
            response = self._client.chat.completions.create(**kwargs)

        message = response.choices[0].message
        content = message.content or ""
        reasoning = getattr(message, "reasoning_content", None) or getattr(
            message, "reasoning", None
        )
        if not content and reasoning:
            content = str(reasoning)
        return parse_json_content(content)


def parse_json_content(content: str) -> dict[str, Any]:
    text = THINK_RE.sub("", content or "").strip()
    if not text:
        raise TokenFactoryError("Nemotron returned an empty completion")
    fenced = FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise TokenFactoryError("Nemotron completion did not contain a JSON object")
    return json.loads(text[start : end + 1])
