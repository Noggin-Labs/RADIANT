"""Transparent scenario-level scoring and aggregate metrics.

Design notes and their limits
-----------------------------
* ``diagnosis_correct`` is an **exact normalized-label match**, not a semantic
  judgement. Two differently worded labels for the same misconception score as
  incorrect. This is conservative and must not be reported as semantic accuracy.
* ``evidence_grounded`` is a **lexical substring check**: every quote supplied by
  the tutor must appear in the student's work. It does not establish that the
  quote logically supports the diagnosis. It is not entailment.
* A failed adapter call is recorded with ``error`` set. Such rows are reported in
  a failure count and are **excluded** from accuracy denominators rather than
  silently counted as wrong. They are never silently dropped either.
* The unsupported-diagnosis rate uses the insufficient-evidence subset as its
  denominator (scenarios whose reference action is not ``diagnose``), because the
  pooled denominator over all scenarios answers a different question.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Iterable

from .models import EvaluationRecord, Scenario, TutorResponse

INSUFFICIENT_EVIDENCE_ACTIONS = frozenset({"ask_clarification", "abstain"})


def normalize_label(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
    return normalized or None


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> list[float] | None:
    """Wilson score interval for a binomial proportion.

    Reported for descriptive uncertainty only: scenarios in a pilot benchmark are
    a convenience sample, not a random sample from a defined population, so the
    interval does not license a population inference.
    """
    if n <= 0:
        return None
    p = successes / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def _rate(flags: list[bool]) -> dict:
    """Rate with explicit numerator, denominator and interval."""
    n = len(flags)
    successes = sum(1 for f in flags if f)
    return {
        "rate": (successes / n) if n else None,
        "numerator": successes,
        "denominator": n,
        "wilson_95ci": wilson_interval(successes, n),
    }


def score_response(scenario: Scenario, response: TutorResponse) -> EvaluationRecord:
    expected_diagnosis = normalize_label(scenario.reference_diagnosis)
    actual_diagnosis = normalize_label(response.diagnosis)
    if scenario.expected_action == "diagnose":
        diagnosis_correct: bool | None = actual_diagnosis == expected_diagnosis
    else:
        diagnosis_correct = None

    action_correct = response.action == scenario.expected_action

    if response.action == "diagnose":
        quotes = [q for q in (response.evidence or ()) if isinstance(q, str)]
        evidence_grounded: bool | None = bool(quotes) and all(
            quote.strip() and quote.casefold() in (scenario.student_work or "").casefold()
            for quote in quotes
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
        expected_action=scenario.expected_action,
        problem=scenario.problem,
        final_answer=scenario.final_answer,
        student_work=scenario.student_work,
    )


def aggregate_metrics(records: Iterable[EvaluationRecord]) -> dict:
    rows = list(records)
    failed = [r for r in rows if r.error is not None]
    scored = [r for r in rows if r.error is None]

    diagnosis_rows = [r for r in scored if r.diagnosis_correct is not None]
    grounding_rows = [r for r in scored if r.evidence_grounded is not None]
    # Denominator for unsupported diagnosis: scenarios that genuinely lack
    # sufficient evidence to justify a diagnosis.
    insufficient_rows = [
        r for r in scored if r.expected_action in INSUFFICIENT_EVIDENCE_ACTIONS
    ]

    by_condition: dict[str, list[EvaluationRecord]] = defaultdict(list)
    for row in rows:
        by_condition[row.condition].append(row)

    return {
        "n_scenarios": len(rows),
        "n_scored": len(scored),
        "n_failures": len(failed),
        "failure_rate": _rate([r.error is not None for r in rows]),
        "failed_scenario_ids": [r.scenario_id for r in failed],
        "n_diagnosis_scenarios": len(diagnosis_rows),
        "action_accuracy": _rate([r.action_correct for r in scored]),
        "diagnosis_accuracy": _rate([bool(r.diagnosis_correct) for r in diagnosis_rows]),
        "evidence_grounding_rate": _rate([bool(r.evidence_grounded) for r in grounding_rows]),
        "unsupported_diagnosis_rate_insufficient_evidence": _rate(
            [r.unsupported_diagnosis for r in insufficient_rows]
        ),
        "n_insufficient_evidence_scenarios": len(insufficient_rows),
        # Retained for continuity with earlier reports. Its denominator is all
        # scored scenarios, so it is NOT the insufficient-evidence rate.
        "unsupported_diagnosis_rate_pooled_legacy": _rate(
            [r.unsupported_diagnosis for r in scored]
        ),
        "diagnosis_accuracy_note": (
            "Exact normalized-label match only. Not semantic accuracy, and not "
            "an assessment of teaching quality."
        ),
        "evidence_grounding_note": (
            "Lexical substring presence of quoted text only. Not logical entailment."
        ),
        "by_condition": {
            condition: {
                "n": len(group),
                "n_scored": sum(1 for r in group if r.error is None),
                "n_failures": sum(1 for r in group if r.error is not None),
                "action_accuracy": _rate(
                    [r.action_correct for r in group if r.error is None]
                ),
                "diagnosis_accuracy": _rate(
                    [
                        bool(r.diagnosis_correct)
                        for r in group
                        if r.error is None and r.diagnosis_correct is not None
                    ]
                ),
                "unsupported_diagnosis_rate_insufficient_evidence": _rate(
                    [
                        r.unsupported_diagnosis
                        for r in group
                        if r.error is None
                        and r.expected_action in INSUFFICIENT_EVIDENCE_ACTIONS
                    ]
                ),
            }
            for condition, group in sorted(by_condition.items())
        },
        "warning": (
            "Aggregate metrics on a synthetic pilot benchmark do not establish "
            "learning gains, causal effects, or validity as an educational assessment."
        ),
    }
