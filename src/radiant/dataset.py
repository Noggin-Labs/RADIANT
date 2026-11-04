"""JSONL dataset loading and structural validation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .models import Scenario

ALLOWED_ACTIONS = {"diagnose", "ask_clarification", "abstain"}

PAIR_CONDITIONS = {
    "counterfactual": ("counterfactual_a", "counterfactual_b"),
    "paraphrase": ("original", "paraphrase"),
}


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


def validate_pairs(scenarios: Iterable[Scenario]) -> dict:
    """Check that matched sets are well formed and structurally equivalent.

    A benchmark whose pairs are broken cannot support counterfactual-sensitivity or
    paraphrase-invariance claims, so these checks run before any model is called.
    Problems are returned as data rather than raised, so that a partially broken
    pilot dataset still produces an inspectable report.
    """
    groups: dict[str, list[Scenario]] = defaultdict(list)
    unpaired: list[str] = []
    for scenario in scenarios:
        if scenario.pair_id:
            groups[scenario.pair_id].append(scenario)
        else:
            unpaired.append(scenario.scenario_id)

    issues: list[dict] = []
    for pair_id, group in sorted(groups.items()):
        counts: dict[str, int] = defaultdict(int)
        for scenario in group:
            counts[scenario.condition] += 1
        for condition, count in counts.items():
            if count > 1:
                issues.append({
                    "pair_id": pair_id,
                    "issue": f"duplicate condition '{condition}' ({count} scenarios)",
                })

        problems = {" ".join((s.problem or "").casefold().split()) for s in group}
        if len(problems) > 1:
            issues.append({"pair_id": pair_id, "issue": "problems differ across the matched set"})

        for kind, (a_cond, b_cond) in PAIR_CONDITIONS.items():
            present = {s.condition for s in group}
            if not (a_cond in present or b_cond in present):
                continue
            if not {a_cond, b_cond} <= present:
                missing = sorted({a_cond, b_cond} - present)
                issues.append({
                    "pair_id": pair_id,
                    "issue": f"incomplete {kind} set; missing {', '.join(missing)}",
                })
                continue
            a = next(s for s in group if s.condition == a_cond)
            b = next(s for s in group if s.condition == b_cond)
            if kind == "counterfactual":
                if (a.final_answer or "") != (b.final_answer or ""):
                    issues.append({
                        "pair_id": pair_id,
                        "issue": "counterfactual conditions state different final answers",
                    })
                if (a.reference_diagnosis or "") == (b.reference_diagnosis or ""):
                    issues.append({
                        "pair_id": pair_id,
                        "issue": "counterfactual conditions share a reference diagnosis",
                    })
                if (a.student_work or "") == (b.student_work or ""):
                    issues.append({
                        "pair_id": pair_id,
                        "issue": "counterfactual conditions have identical student work",
                    })
            else:
                if (a.reference_diagnosis or "") != (b.reference_diagnosis or ""):
                    issues.append({
                        "pair_id": pair_id,
                        "issue": "paraphrase conditions have different reference diagnoses",
                    })
                if (a.student_work or "") == (b.student_work or ""):
                    issues.append({
                        "pair_id": pair_id,
                        "issue": "paraphrase conditions have identical student work",
                    })

    return {
        "n_matched_sets": len(groups),
        "n_scenarios_without_pair_id": len(unpaired),
        "issues": issues,
        "valid": not issues,
        "note": (
            "Structural checks only. They cannot establish that a pair is a "
            "mathematically meaningful counterfactual; that needs human review."
        ),
    }


def ensure_unique_ids(scenarios: Iterable[Scenario]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for scenario in scenarios:
        if scenario.scenario_id in seen:
            duplicates.add(scenario.scenario_id)
        seen.add(scenario.scenario_id)
    if duplicates:
        raise ValueError(f"Duplicate scenario IDs: {', '.join(sorted(duplicates))}")
