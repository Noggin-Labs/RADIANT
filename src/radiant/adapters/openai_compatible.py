"""Adapter for OpenAI-compatible chat-completions APIs using the optional httpx extra."""

from __future__ import annotations

import json
import os
import re

from radiant.adapters.base import TutorAdapter
from radiant.models import Scenario, TutorResponse
from radiant.prompting import SYSTEM_PROMPT, build_user_prompt


class OpenAICompatibleAdapter(TutorAdapter):
    name = "openai-compatible"

    def __init__(self, model: str | None = None, base_url: str | None = None,
                 api_key: str | None = None, temperature: float = 0.0,
                 timeout: float = 60.0):
        try:
            import httpx  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("Install the API extra with: pip install -e '.[api]'") from exc
        self.model = model or os.getenv("RADIANT_MODEL")
        self.base_url = (base_url or os.getenv("RADIANT_API_BASE", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("RADIANT_API_KEY")
        self.temperature = temperature
        self.timeout = timeout
        if not self.model:
            raise ValueError("Set RADIANT_MODEL or pass model=...")
        if not self.api_key:
            raise ValueError("Set RADIANT_API_KEY or pass api_key=...")

    def respond(self, scenario: Scenario) -> TutorResponse:
        import httpx

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": self.temperature,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(scenario)},
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return parse_tutor_json(content)


def parse_tutor_json(content: str) -> TutorResponse:
    """Parse strict JSON, tolerating a single surrounding Markdown code fence."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Tutor response was not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Tutor response JSON must be an object")
    action = payload.get("action")
    if action not in {"diagnose", "ask_clarification", "abstain"}:
        raise ValueError(f"Unsupported tutor action: {action!r}")
    diagnosis = payload.get("diagnosis")
    if diagnosis is not None and not isinstance(diagnosis, str):
        raise ValueError("diagnosis must be a string or null")
    evidence = payload.get("evidence", [])
    if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
        raise ValueError("evidence must be an array of strings")
    if action != "diagnose" and diagnosis is not None:
        raise ValueError("Non-diagnostic actions must return diagnosis=null")
    return TutorResponse.from_dict(payload, raw_text=content)
