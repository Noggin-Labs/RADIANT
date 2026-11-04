#!/usr/bin/env python3
"""Adversarial probes of the corrected RADIANT metrics.

Each probe constructs a case where a naive metric would have reported success while
the evaluated behaviour is logically wrong, and asserts what the corrected metric
reports. This is the independent review of the previous sprint's corrections.

Probes are written as data, not as pytest cases, so the output is a table that can be
read in an audit report. Exit status is non-zero if any probe contradicts the
expected corrected behaviour.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radiant.analysis import paired_diagnostics  # noqa: E402
from radiant.dataset import validate_pairs  # noqa: E402
from radiant.models import EvaluationRecord, Scenario, TutorResponse  # noqa: E402
from radiant.scoring import aggregate_metrics, score_response  # noqa: E402


def scenario(sid, condition, *, pair_id=None, ref=None, problem="Solve 3x = 12.",
             work="3x = 12; x = 4", final="x = 4", action="diagnose"):
    return Scenario(
        scenario_id=sid, condition=condition, problem=problem,
        final_answer=final, student_work=work if action == "diagnose" else None,
        reference_diagnosis=ref, expected_action=action, pair_id=pair_id,
    )


def rec(sc, diagnosis, *, action="diagnose", evidence=(), error=None):
    r = score_response(sc, TutorResponse(diagnosis, action, evidence=evidence))
    r.error = error
    return r


def probe(name, threat, condition_succeeded, explanation):
    return {
        "probe": name,
        "threat": threat,
        "metric_should_report_success": False,
        "metric_actually_reported_success": bool(condition_succeeded),
        "verdict": "DEFENDED" if not condition_succeeded else "BYPASSED",
        "explanation": explanation,
    }


def main() -> int:
    results = []

    # P1: two different but both wrong labels.
    a = scenario("a", "counterfactual_a", pair_id="p1", ref="correct_reasoning", work="3x = 12; x = 4")
    b = scenario("b", "counterfactual_b", pair_id="p1", ref="invalid_operation", work="3x = 11; x = 4")
    d = paired_diagnostics([rec(a, "nonsense_one"), rec(b, "nonsense_two")])
    results.append(probe(
        "P1_two_wrong_different_labels",
        "Different-but-wrong outputs look like reasoning sensitivity.",
        d["counterfactual_sensitivity"]["rate"] == 1.0,
        f"sensitivity={d['counterfactual_sensitivity']}",
    ))

    # P2: both diagnoses missing.
    a = scenario("a", "original", pair_id="p2", ref="correct_reasoning")
    b = scenario("b", "paraphrase", pair_id="p2", ref="correct_reasoning", work="other wording")
    d = paired_diagnostics([rec(a, None, action="abstain"), rec(b, None, action="abstain")])
    results.append(probe(
        "P2_both_outputs_missing",
        "Two absent diagnoses look like paraphrase invariance.",
        d["paraphrase_invariance"]["rate"] == 1.0,
        f"invariance={d['paraphrase_invariance']}",
    ))

    # P3: one correct, one wrong, different labels.
    a = scenario("a", "counterfactual_a", pair_id="p3", ref="correct_reasoning")
    b = scenario("b", "counterfactual_b", pair_id="p3", ref="invalid_operation", work="3x = 11; x = 4")
    d = paired_diagnostics([rec(a, "correct reasoning"), rec(b, "something else")])
    results.append(probe(
        "P3_one_correct_one_wrong",
        "One accurate and one inaccurate label counts as sensitivity.",
        d["counterfactual_sensitivity"]["rate"] == 1.0,
        f"sensitivity={d['counterfactual_sensitivity']}",
    ))

    # P4: duplicate condition in a matched set.
    a1 = scenario("a1", "counterfactual_a", pair_id="p4", ref="correct_reasoning")
    a2 = scenario("a2", "counterfactual_a", pair_id="p4", ref="correct_reasoning", work="3x = 12; x = 4 again")
    b = scenario("b", "counterfactual_b", pair_id="p4", ref="invalid_operation", work="3x = 11; x = 4")
    d = paired_diagnostics([rec(a1, "x"), rec(a2, "x"), rec(b, "y")])
    results.append(probe(
        "P4_duplicate_condition",
        "A duplicated condition is silently collapsed and the pair scored.",
        d["counterfactual_sensitivity"]["denominator"] > 0,
        f"denominator={d['counterfactual_sensitivity']['denominator']}, invalid={len(d['invalid_pairs'])}",
    ))

    # P5: a failed call inside a pair.
    a = scenario("a", "original", pair_id="p5", ref="correct_reasoning")
    b = scenario("b", "paraphrase", pair_id="p5", ref="correct_reasoning", work="other wording")
    d = paired_diagnostics([
        rec(a, "correct reasoning"),
        rec(b, None, action="error", error="TimeoutError: timed out"),
    ])
    results.append(probe(
        "P5_failed_call_in_pair",
        "An infrastructure failure is scored as a successful pair.",
        d["paraphrase_invariance"]["denominator"] > 0,
        f"denominator={d['paraphrase_invariance']['denominator']}",
    ))

    # P6: failure counted as a wrong answer (denominator contamination).
    sc = scenario("f", "original", ref="correct_reasoning")
    m = aggregate_metrics([rec(sc, None, action="error", error="TimeoutError")])
    results.append(probe(
        "P6_failure_deflects_accuracy",
        "A failed call is included in the accuracy denominator as wrong.",
        m["diagnosis_accuracy"]["denominator"] > 0,
        f"diagnosis denominator={m['diagnosis_accuracy']['denominator']}, failures={m['n_failures']}",
    ))

    # P7: unsupported rate against the wrong denominator.
    diag_sc = scenario("d1", "original", ref="correct_reasoning")
    under = scenario("u1", "underdetermined", action="ask_clarification")
    m = aggregate_metrics([rec(diag_sc, "correct reasoning"), rec(under, "careless arithmetic")])
    results.append(probe(
        "P7_wrong_unsupported_denominator",
        "Unsupported-diagnosis rate diluted by scenarios where a diagnosis was justified.",
        m["unsupported_diagnosis_rate_insufficient_evidence"]["denominator"] != 1,
        f"insufficient denominator={m['unsupported_diagnosis_rate_insufficient_evidence']['denominator']}",
    ))

    # P8: paraphrase pair whose reference labels differ.
    a = scenario("a", "original", pair_id="p8", ref="correct_reasoning")
    b = scenario("b", "paraphrase", pair_id="p8", ref="arithmetic_error", work="other wording")
    v = validate_pairs([a, b])
    results.append(probe(
        "P8_mislabelled_pair",
        "A 'paraphrase' pair with different reference labels is treated as valid.",
        v["valid"],
        f"issues={len(v['issues'])}",
    ))

    # P9: labels identical after normalisation only.
    a = scenario("a", "counterfactual_a", pair_id="p9", ref="Correct  Reasoning")
    b = scenario("b", "counterfactual_b", pair_id="p9", ref="correct-reasoning!", work="3x = 11; x = 4")
    d = paired_diagnostics([rec(a, "Correct reasoning"), rec(b, "correct_reasoning")])
    results.append(probe(
        "P9_normalisation_collapses_labels",
        "Two labels that differ only in punctuation are counted as genuine sensitivity.",
        d["counterfactual_sensitivity"]["rate"] == 1.0,
        f"sensitivity={d['counterfactual_sensitivity']}",
    ))

    # P10: legitimate pair must still succeed (no over-blocking).
    a = scenario("a", "counterfactual_a", pair_id="p10", ref="correct_reasoning", work="3x = 12; x = 4")
    b = scenario("b", "counterfactual_b", pair_id="p10", ref="invalid_operation", work="3x = 11; x = 4")
    d = paired_diagnostics([rec(a, "Correct reasoning"), rec(b, "Invalid operation")])
    ok = d["counterfactual_sensitivity"]["rate"] == 1.0
    results.append({
        "probe": "P10_legitimate_pair_still_passes",
        "threat": "Over-blocking: a correct pair is wrongly rejected.",
        "metric_should_report_success": True,
        "metric_actually_reported_success": bool(ok),
        "verdict": "DEFENDED" if ok else "OVER_BLOCKED",
        "explanation": f"sensitivity={d['counterfactual_sensitivity']}",
    })

    print(json.dumps({"probes": results}, indent=2))

    failures = [r for r in results if (r["metric_actually_reported_success"]
                                       != r["metric_should_report_success"])]
    print(f"\n{len(results) - len(failures)}/{len(results)} probes behaved as required")
    for f in failures:
        print(f"  MISMATCH: {f['probe']} -> {f['verdict']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
