"""JSONL dataset loading and structural validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import Scenario

ALLOWED_ACTIONS = {"diagnose", "ask_clarification", "abstain"}


def load_jsonl(path: str | Path) -> list[Scenario]:
    scenarios: list[Scenario] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            try:
                raw = json.loads(line)
                scenario = Scenario.from_dict(raw)
                validate_scenario(scenario)
                scenarios.append(scenario)
            except Exception as exc:
                raise ValueError(f"Invalid dataset row at {path}:{line_number}: {exc}") from exc
    ensure_unique_ids(scenarios)
    return scenarios


def validate_scenario(scenario: Scenario) -> None:
    if not scenario.scenario_id.strip():
        raise ValueError("scenario_id cannot be empty")
    if scenario.expected_action not in ALLOWED_ACTIONS:
        raise ValueError(f"expected_action must be one of {sorted(ALLOWED_ACTIONS)}")
    if not scenario.problem.strip():
        raise ValueError("problem cannot be empty")
    if scenario.expected_action == "diagnose" and not scenario.reference_diagnosis:
        raise ValueError("diagnosis scenarios require reference_diagnosis")
    if scenario.expected_action != "diagnose" and scenario.reference_diagnosis is not None:
        raise ValueError("clarification/abstention scenarios must not provide a diagnosis label")
    if scenario.expected_action == "ask_clarification" and scenario.student_work:
        raise ValueError("clarification scenarios should explicitly represent missing/insufficient work")


def ensure_unique_ids(scenarios: Iterable[Scenario]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for scenario in scenarios:
        if scenario.scenario_id in seen:
            duplicates.add(scenario.scenario_id)
        seen.add(scenario.scenario_id)
    if duplicates:
        raise ValueError(f"Duplicate scenario IDs: {', '.join(sorted(duplicates))}")
