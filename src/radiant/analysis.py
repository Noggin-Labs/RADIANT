"""Matched-pair diagnostics for counterfactual sensitivity and paraphrase invariance.

Three corrections relative to the first implementation
------------------------------------------------------
1. **Correctness-aware counterfactual sensitivity.** A tutor that emits two
   *different but both wrong* labels is not sensitive to reasoning; it is noisy.
   A counterfactual pair now succeeds only when both diagnoses are present,
   each is correct against its own reference, and they differ.
2. **Missingness-aware paraphrase invariance.** Two absent diagnoses are not
   evidence of invariance. A paraphrase pair now succeeds only when both
   diagnoses are present, both are correct, and they agree.
3. **Pair validation.** Duplicate conditions, structurally non-equivalent pairs,
   and incomplete pairs are reported explicitly instead of being silently
   collapsed by a dictionary comprehension.

Every rate reports its own numerator and denominator so that no rate can be read
against the wrong base.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import EvaluationRecord
from .scoring import INSUFFICIENT_EVIDENCE_ACTIONS, normalize_label

EXPECTED_CONDITIONS = {
    "counterfactual": ("counterfactual_a", "counterfactual_b"),
    "paraphrase": ("original", "paraphrase"),
}


def _norm_text(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _rate(flags: list[bool]) -> dict:
    n = len(flags)
    successes = sum(1 for f in flags if f)
    return {
        "rate": (successes / n) if n else None,
        "numerator": successes,
        "denominator": n,
    }


def _pair_issues(
    pair_id: str,
    group: list[EvaluationRecord],
    kind: str,
) -> list[str]:
    """Structural validity checks for one matched set."""
    issues: list[str] = []
    a_cond, b_cond = EXPECTED_CONDITIONS[kind]

    counts: dict[str, int] = defaultdict(int)
    for record in group:
        counts[record.condition] += 1
    for condition, count in counts.items():
        if count > 1:
            issues.append(f"duplicate condition '{condition}' appears {count} times")

    present = set(counts)
    missing = {a_cond, b_cond} - present
    if missing:
        issues.append(f"missing condition(s): {', '.join(sorted(missing))}")

    if missing:
        return issues

    a = next(r for r in group if r.condition == a_cond)
    b = next(r for r in group if r.condition == b_cond)

    if _norm_text(a.problem) != _norm_text(b.problem):
        issues.append("problems differ between paired conditions")

    if kind == "counterfactual":
        # A counterfactual pair is only interpretable if the confound is what
        # changed. The stated final answer must match while the reference
        # diagnosis differs; otherwise "different diagnosis" is unsurprising.
        if _norm_text(a.final_answer) != _norm_text(b.final_answer):
            issues.append("final answers differ; pair is not a controlled counterfactual")
        if normalize_label(a.reference_diagnosis) == normalize_label(b.reference_diagnosis):
            issues.append("reference diagnoses are identical; pair cannot test sensitivity")
        if _norm_text(a.student_work) == _norm_text(b.student_work):
            issues.append("student work is identical; no reasoning change to detect")
    else:
        # A paraphrase pair must hold the reasoning fixed while the wording changes.
        if normalize_label(a.reference_diagnosis) != normalize_label(b.reference_diagnosis):
            issues.append("reference diagnoses differ; pair is not a paraphrase pair")
        if _norm_text(a.student_work) == _norm_text(b.student_work):
            issues.append("student work is identical; the pair is not a paraphrase")

    if any(r.error is not None for r in (a, b)):
        issues.append("one or both conditions failed at the adapter level")
    return issues


def paired_diagnostics(records: Iterable[EvaluationRecord]) -> dict:
    groups: dict[str, list[EvaluationRecord]] = defaultdict(list)
    unpaired: list[str] = []
    for record in records:
        if record.pair_id:
            groups[record.pair_id].append(record)
        else:
            unpaired.append(record.scenario_id)

    sensitivity_pairs: list[dict] = []
    paraphrase_pairs: list[dict] = []
    invalid: list[dict] = []

    for pair_id, group in sorted(groups.items()):
        conditions = {record.condition for record in group}
        kinds = [
            kind
            for kind, (a_cond, b_cond) in EXPECTED_CONDITIONS.items()
            if a_cond in conditions or b_cond in conditions
        ]
        if not kinds:
            invalid.append({
                "pair_id": pair_id,
                "conditions": sorted(conditions),
                "issues": ["no recognised condition names in this matched set"],
            })
            continue

        for kind in kinds:
            issues = _pair_issues(pair_id, group, kind)
            if issues:
                invalid.append({
                    "pair_id": pair_id,
                    "kind": kind,
                    "conditions": sorted(conditions),
                    "issues": issues,
                })
                continue

            a_cond, b_cond = EXPECTED_CONDITIONS[kind]
            a = next(r for r in group if r.condition == a_cond)
            b = next(r for r in group if r.condition == b_cond)

            if kind == "counterfactual":
                present = (
                    normalize_label(a.response.diagnosis) is not None
                    and normalize_label(b.response.diagnosis) is not None
                )
                both_correct = a.diagnosis_correct is True and b.diagnosis_correct is True
                different = (
                    normalize_label(a.response.diagnosis)
                    != normalize_label(b.response.diagnosis)
                )
                sensitivity_pairs.append({
                    "pair_id": pair_id,
                    "reference_diagnoses_differ": True,
                    "both_responses_present": present,
                    "both_diagnoses_correct": both_correct,
                    "observed_differ": different,
                    "success": bool(present and both_correct and different),
                })
            else:
                present = (
                    normalize_label(a.response.diagnosis) is not None
                    and normalize_label(b.response.diagnosis) is not None
                )
                both_correct = a.diagnosis_correct is True and b.diagnosis_correct is True
                same = (
                    normalize_label(a.response.diagnosis)
                    == normalize_label(b.response.diagnosis)
                )
                paraphrase_pairs.append({
                    "pair_id": pair_id,
                    "both_responses_present": present,
                    "both_diagnoses_correct": both_correct,
                    "observed_same": same,
                    "success": bool(present and both_correct and same),
                })

    n_invalid = len(invalid)
    n_groups = len(groups)
    return {
        "counterfactual_sensitivity": _rate([p["success"] for p in sensitivity_pairs]),
        "counterfactual_pairs": sensitivity_pairs,
        "counterfactual_missing_response_count": sum(
            1 for p in sensitivity_pairs if not p["both_responses_present"]
        ),
        "counterfactual_partially_incorrect_count": sum(
            1
            for p in sensitivity_pairs
            if p["both_responses_present"] and not p["both_diagnoses_correct"]
        ),
        "paraphrase_invariance": _rate([p["success"] for p in paraphrase_pairs]),
        "paraphrase_pairs": paraphrase_pairs,
        "paraphrase_missing_response_count": sum(
            1 for p in paraphrase_pairs if not p["both_responses_present"]
        ),
        "paraphrase_partially_incorrect_count": sum(
            1
            for p in paraphrase_pairs
            if p["both_responses_present"] and not p["both_diagnoses_correct"]
        ),
        "invalid_pairs": invalid,
        "pair_denominators": {
            "matched_sets_total": n_groups,
            "invalid_matched_sets": n_invalid,
            "counterfactual_sets_evaluable": len(sensitivity_pairs),
            "paraphrase_sets_evaluable": len(paraphrase_pairs),
            "scenarios_without_pair_id": len(unpaired),
        },
        "note": (
            "Only explicitly paired scenarios are evaluated. Invalid or incomplete "
            "matched sets are reported above and excluded from the rates, not "
            "silently dropped. A success here means 'produced the right label for "
            "both conditions', not 'reasoned correctly'."
        ),
        "insufficient_evidence_actions": sorted(INSUFFICIENT_EVIDENCE_ACTIONS),
    }
