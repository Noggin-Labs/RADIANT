"""Regression tests for the metric defects found in the RADIANT audit.

Each test names the specific validity failure it prevents from returning.
"""

import pytest

from radiant.analysis import paired_diagnostics
from radiant.dataset import validate_pairs
from radiant.models import EvaluationRecord, Scenario, TutorResponse
from radiant.scoring import aggregate_metrics, score_response, wilson_interval


def _scenario(sid, condition, *, pair_id=None, ref=None, problem="Solve 3x = 12.",
              work="3x = 12; x = 4", final="x = 4", action="diagnose"):
    return Scenario(
        scenario_id=sid, condition=condition, problem=problem,
        final_answer=final, student_work=work if action == "diagnose" else None,
        reference_diagnosis=ref, expected_action=action, pair_id=pair_id,
    )


def _rec(scenario, diagnosis, *, action="diagnose", evidence=(), error=None):
    record = score_response(scenario, TutorResponse(diagnosis, action, evidence=evidence))
    record.error = error
    return record


# --- 1. Counterfactual sensitivity requires correctness, not mere difference ----

def test_counterfactual_two_wrong_but_different_labels_is_not_sensitivity():
    a = _scenario("a", "counterfactual_a", pair_id="p1", ref="correct_reasoning",
                  work="3x = 12; x = 4")
    b = _scenario("b", "counterfactual_b", pair_id="p1", ref="invalid_operation",
                  work="3x = 11; x = 4")
    records = [
        _rec(a, "wildly_wrong_one"),
        _rec(b, "wildly_wrong_two"),
    ]
    diag = paired_diagnostics(records)
    assert diag["counterfactual_sensitivity"]["numerator"] == 0
    assert diag["counterfactual_sensitivity"]["denominator"] == 1
    assert diag["counterfactual_pairs"][0]["observed_differ"] is True
    assert diag["counterfactual_pairs"][0]["success"] is False


def test_counterfactual_both_correct_and_different_is_sensitivity():
    a = _scenario("a", "counterfactual_a", pair_id="p2", ref="correct reasoning")
    b = _scenario("b", "counterfactual_b", pair_id="p2", ref="invalid operation",
                  work="3x = 11; x = 4")
    diag = paired_diagnostics([_rec(a, "Correct reasoning"), _rec(b, "Invalid operation")])
    assert diag["counterfactual_sensitivity"]["numerator"] == 1
    assert diag["counterfactual_sensitivity"]["denominator"] == 1


# --- 2. Missing outputs must not count as paraphrase invariance -----------------

def test_paraphrase_with_both_missing_diagnoses_is_not_invariance():
    a = _scenario("a", "original", pair_id="q1", ref="correct_reasoning")
    b = _scenario("b", "paraphrase", pair_id="q1", ref="correct_reasoning",
                  work="I divided both sides by three, so x is four.")
    diag = paired_diagnostics([_rec(a, None, action="abstain"), _rec(b, None, action="abstain")])
    assert diag["paraphrase_invariance"]["numerator"] == 0
    assert diag["paraphrase_invariance"]["denominator"] == 1
    assert diag["paraphrase_missing_response_count"] == 1


def test_paraphrase_with_one_missing_diagnosis_is_not_invariance():
    a = _scenario("a", "original", pair_id="q2", ref="correct_reasoning")
    b = _scenario("b", "paraphrase", pair_id="q2", ref="correct_reasoning",
                  work="Dividing by three gives four.")
    diag = paired_diagnostics([_rec(a, "correct reasoning"), _rec(b, None, action="abstain")])
    assert diag["paraphrase_invariance"]["numerator"] == 0


# --- 3./4. Duplicate and incomplete pair conditions must be detected -----------

def test_duplicate_condition_in_pair_is_reported_not_silently_collapsed():
    a1 = _scenario("a1", "counterfactual_a", pair_id="dup", ref="correct_reasoning")
    a2 = _scenario("a2", "counterfactual_a", pair_id="dup", ref="correct_reasoning",
                   work="3x = 12; x = 4 (again)")
    b = _scenario("b", "counterfactual_b", pair_id="dup", ref="invalid_operation",
                  work="3x = 11; x = 4")
    diag = paired_diagnostics([_rec(a1, "x"), _rec(a2, "x"), _rec(b, "y")])
    assert diag["counterfactual_sensitivity"]["denominator"] == 0
    assert diag["invalid_pairs"]
    assert any("duplicate condition" in i for i in diag["invalid_pairs"][0]["issues"])


def test_incomplete_pair_is_reported():
    a = _scenario("a", "counterfactual_a", pair_id="half", ref="correct_reasoning")
    diag = paired_diagnostics([_rec(a, "correct reasoning")])
    assert diag["counterfactual_sensitivity"]["denominator"] == 0
    assert any("missing condition" in " ".join(i["issues"]) for i in diag["invalid_pairs"])


def test_pair_with_different_problems_is_rejected():
    a = _scenario("a", "original", pair_id="p3", ref="r", problem="Solve 2x=4.")
    b = _scenario("b", "paraphrase", pair_id="p3", ref="r", problem="Solve 5x=10.",
                  work="different wording")
    issues = validate_pairs([a, b])["issues"]
    assert any("problems differ" in i["issue"] for i in issues)


def test_identical_counterfactual_work_is_rejected():
    a = _scenario("a", "counterfactual_a", pair_id="p4", ref="ok", work="same work")
    b = _scenario("b", "counterfactual_b", pair_id="p4", ref="bad", work="same work")
    issues = validate_pairs([a, b])["issues"]
    assert any("identical student work" in i["issue"] for i in issues)


# --- 5. Unsupported-diagnosis rate needs the right denominator ----------------

def test_unsupported_rate_uses_insufficient_evidence_denominator():
    diagnose_scen = _scenario("d1", "original", ref="correct_reasoning")
    under = _scenario("u1", "underdetermined", action="ask_clarification")
    under2 = _scenario("u2", "answer_only", action="abstain")
    records = [
        _rec(diagnose_scen, "correct reasoning"),
        _rec(under, "careless arithmetic"),      # unsupported
        _rec(under2, None, action="abstain"),    # correct abstention
    ]
    metrics = aggregate_metrics(records)
    subset = metrics["unsupported_diagnosis_rate_insufficient_evidence"]
    assert subset["denominator"] == 2
    assert subset["numerator"] == 1
    assert subset["rate"] == pytest.approx(0.5)
    # The legacy pooled rate must remain visibly different.
    assert metrics["unsupported_diagnosis_rate_pooled_legacy"]["denominator"] == 3


# --- 6. Lexical evidence matching is not entailment ---------------------------

def test_evidence_check_is_substring_only_and_documented_as_such():
    scenario = _scenario("e1", "original", ref="arithmetic error",
                         work="2 + 2 = 5")
    # The quote exists verbatim but does not support the diagnosis.
    record = score_response(
        scenario,
        TutorResponse("Arithmetic error", "diagnose", evidence=("2 + 2 = 5",)),
    )
    assert record.evidence_grounded is True
    metrics = aggregate_metrics([record])
    assert "not logical entailment" in metrics["evidence_grounding_note"].lower()


def test_fabricated_evidence_quote_is_not_grounded():
    scenario = _scenario("e2", "original", ref="arithmetic error", work="2 + 2 = 5")
    record = score_response(
        scenario, TutorResponse("Arithmetic error", "diagnose", evidence=("2 + 2 = 4",))
    )
    assert record.evidence_grounded is False


# --- 7. Failed model calls must stay visible and out of accuracy denominators --

def test_failed_call_is_counted_as_failure_not_as_wrong_answer():
    scenario = _scenario("f1", "original", ref="correct_reasoning")
    record = _rec(scenario, None, action="error", error="TimeoutError: timed out")
    metrics = aggregate_metrics([record])
    assert metrics["n_failures"] == 1
    assert metrics["failure_rate"]["numerator"] == 1
    assert metrics["failure_rate"]["denominator"] == 1
    assert metrics["n_scored"] == 0
    assert metrics["diagnosis_accuracy"]["denominator"] == 0
    assert metrics["diagnosis_accuracy"]["rate"] is None
    assert metrics["failed_scenario_ids"] == ["f1"]


def test_failure_in_pair_invalidates_the_pair():
    a = _scenario("a", "original", pair_id="z1", ref="correct_reasoning")
    b = _scenario("b", "paraphrase", pair_id="z1", ref="correct_reasoning",
                  work="other wording")
    diag = paired_diagnostics([
        _rec(a, "correct reasoning"),
        _rec(b, None, action="error", error="TimeoutError: timed out"),
    ])
    assert diag["paraphrase_invariance"]["denominator"] == 0
    assert any("adapter level" in " ".join(i["issues"]) for i in diag["invalid_pairs"])


# --- 8. Explicit strings are exact-matched, and that is documented -------------

def test_semantically_equivalent_labels_are_exact_matched_and_documented():
    scenario = _scenario("s1", "original", ref="invalid intermediate operation")
    record = score_response(
        scenario, TutorResponse("An invalid operation in the middle", "diagnose",
                                evidence=("3x = 12",))
    )
    assert record.diagnosis_correct is False
    assert "not semantic accuracy" in aggregate_metrics([record])["diagnosis_accuracy_note"].lower()


def test_wilson_interval_is_bounded_and_zero_denominator_is_none():
    assert wilson_interval(0, 0) is None
    lo, hi = wilson_interval(0, 10)
    assert 0.0 <= lo <= hi < 1.0
    lo2, hi2 = wilson_interval(10, 10)
    assert 0.0 < lo2 <= hi2 <= 1.0
