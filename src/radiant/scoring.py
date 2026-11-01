"""Transparent scenario-level scoring and aggregate metrics."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from .models import EvaluationRecord, Scenario, TutorResponse


def normalize_label(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def score_response(scenario: Scenario, response: TutorResponse) -> EvaluationRecord:
    expected_diagnosis = normalize_label(scenario.reference_diagnosis)
    actual_diagnosis = normalize_label(response.diagnosis)
    diagnosis_correct: bool | None
    if scenario.expected_action == "diagnose":
        diagnosis_correct = actual_diagnosis == expected_diagnosis
    else:
        diagnosis_correct = None

    action_correct = response.action == scenario.expected_action
    if response.action == "diagnose":
        evidence_grounded: bool | None = bool(response.evidence) and all(
            quote.strip() and quote.casefold() in (scenario.student_work or "").casefold()
            for quote in response.evidence
        )
    else:
        evidence_grounded = None

    unsupported = response.action == "diagnose" and scenario.expected_action != "diagnose"
    return EvaluationRecord(
        scenario_id=scenario.scenario_id,
        condition=scenario.condition,
        pair_id=scenario.pair_id,
        reference_diagnosis=scenario.reference_diagnosis,
        response=response,
        diagnosis_correct=diagnosis_correct,
        action_correct=action_correct,
        evidence_grounded=evidence_grounded,
        unsupported_diagnosis=unsupported,
    )


def aggregate_metrics(records: Iterable[EvaluationRecord]) -> dict:
    rows = list(records)
    diagnosis_rows = [r for r in rows if r.diagnosis_correct is not None]
    action_accuracy = _mean([r.action_correct for r in rows])
    diagnosis_accuracy = _mean([r.diagnosis_correct for r in diagnosis_rows])
    grounding_rows = [r for r in rows if r.evidence_grounded is not None]
    grounding_rate = _mean([r.evidence_grounded for r in grounding_rows])
    unsupported_rate = _mean([r.unsupported_diagnosis for r in rows])

    by_condition: dict[str, list[EvaluationRecord]] = defaultdict(list)
    for row in rows:
        by_condition[row.condition].append(row)

    return {
        "n_scenarios": len(rows),
        "n_diagnosis_scenarios": len(diagnosis_rows),
        "action_accuracy": action_accuracy,
        "diagnosis_accuracy": diagnosis_accuracy,
        "evidence_grounding_rate": grounding_rate,
        "unsupported_diagnosis_rate": unsupported_rate,
        "by_condition": {
            condition: {
                "n": len(group),
                "action_accuracy": _mean([r.action_correct for r in group]),
                "diagnosis_accuracy": _mean([r.diagnosis_correct for r in group if r.diagnosis_correct is not None]),
                "unsupported_diagnosis_rate": _mean([r.unsupported_diagnosis for r in group]),
            }
            for condition, group in sorted(by_condition.items())
        },
        "warning": "Aggregate metrics do not establish learning gains or causal effects.",
    }


def _mean(values: list[bool | float]) -> float | None:
    if not values:
        return None
    return sum(float(value) for value in values) / len(values)
