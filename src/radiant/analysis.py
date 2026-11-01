"""Matched-pair diagnostics for counterfactual sensitivity and paraphrase invariance."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .models import EvaluationRecord
from .scoring import normalize_label


def paired_diagnostics(records: Iterable[EvaluationRecord]) -> dict:
    groups: dict[str, list[EvaluationRecord]] = defaultdict(list)
    for record in records:
        if record.pair_id:
            groups[record.pair_id].append(record)

    sensitivity_pairs = []
    paraphrase_pairs = []
    for pair_id, group in groups.items():
        by_condition = {record.condition: record for record in group}
        if "counterfactual_a" in by_condition and "counterfactual_b" in by_condition:
            a, b = by_condition["counterfactual_a"], by_condition["counterfactual_b"]
            expected_different = normalize_label(a.reference_diagnosis) != normalize_label(b.reference_diagnosis)
            observed_different = normalize_label(a.response.diagnosis) != normalize_label(b.response.diagnosis)
            sensitivity_pairs.append({
                "pair_id": pair_id,
                "expected_to_differ": expected_different,
                "observed_differ": observed_different,
                "success": expected_different and observed_different,
            })
        if "original" in by_condition and "paraphrase" in by_condition:
            a, b = by_condition["original"], by_condition["paraphrase"]
            expected_same = normalize_label(a.reference_diagnosis) == normalize_label(b.reference_diagnosis)
            observed_same = normalize_label(a.response.diagnosis) == normalize_label(b.response.diagnosis)
            paraphrase_pairs.append({
                "pair_id": pair_id,
                "expected_same": expected_same,
                "observed_same": observed_same,
                "success": expected_same and observed_same,
            })

    return {
        "counterfactual_sensitivity": _rate(sensitivity_pairs),
        "counterfactual_pairs": sensitivity_pairs,
        "paraphrase_invariance": _rate(paraphrase_pairs),
        "paraphrase_pairs": paraphrase_pairs,
        "note": "Only explicitly paired scenarios are included; missing or malformed pairs are not inferred.",
    }


def _rate(rows: list[dict]) -> float | None:
    if not rows:
        return None
    return sum(bool(row["success"]) for row in rows) / len(rows)
