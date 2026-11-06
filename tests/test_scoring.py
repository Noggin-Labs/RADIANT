from radiant.models import Scenario, TutorResponse
from radiant.scoring import score_response, aggregate_metrics


def test_exact_diagnosis_and_grounded_quote():
    scenario = Scenario(
        scenario_id="s1", condition="original", problem="2x=4", final_answer="2",
        student_work="2x=4; x=2", reference_diagnosis="correct reasoning",
        evidence_steps=("x=2",), expected_action="diagnose"
    )
    response = TutorResponse("Correct reasoning", "diagnose", evidence=("x=2",))
    record = score_response(scenario, response)
    assert record.diagnosis_correct is True
    assert record.evidence_grounded is True


def test_unsupported_diagnosis_flagged():
    scenario = Scenario(
        scenario_id="s2", condition="underdetermined", problem="x+1=2", final_answer="1",
        student_work=None, reference_diagnosis=None, expected_action="ask_clarification"
    )
    record = score_response(scenario, TutorResponse("careless arithmetic", "diagnose"))
    assert record.unsupported_diagnosis is True
    assert record.action_correct is False


def test_metrics_do_not_report_empty_diagnosis_accuracy_as_zero():
    scenario = Scenario("s3", "under", "x+1=2", "1", None, None, expected_action="abstain")
    record = score_response(scenario, TutorResponse(None, "abstain"))
    # Rates are now dicts so every rate carries its own denominator.
    metrics = aggregate_metrics([record])[
        "diagnosis_accuracy"
    ]
    assert metrics["rate"] is None
    assert metrics["denominator"] == 0


def test_unsupported_diagnosis_rate_uses_insufficient_evidence_subset():
    insufficient = Scenario(
        scenario_id="s4",
        condition="underdetermined",
        problem="x + y = 3",
        final_answer=None,
        student_work="x = 1",
        reference_diagnosis=None,
        expected_action="ask_clarification",
    )
    answerable = Scenario(
        scenario_id="s5",
        condition="answerable",
        problem="2x = 4",
        final_answer="2",
        student_work="2x = 4; x = 2",
        reference_diagnosis="correct reasoning",
        expected_action="diagnose",
    )

    records = [
        score_response(
            insufficient,
            TutorResponse("careless arithmetic", "diagnose"),
        ),
        score_response(
            answerable,
            TutorResponse("correct reasoning", "diagnose"),
        ),
    ]
    metrics = aggregate_metrics(records)

    subset_rate = metrics["unsupported_diagnosis_rate_insufficient_evidence"]
    pooled_rate = metrics["unsupported_diagnosis_rate_pooled_legacy"]

    assert subset_rate["numerator"] == 1
    assert subset_rate["denominator"] == 1
    assert subset_rate["rate"] == 1.0
    assert pooled_rate["numerator"] == 1
    assert pooled_rate["denominator"] == 2
    assert pooled_rate["rate"] == 0.5
