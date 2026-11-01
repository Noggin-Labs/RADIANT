import pytest

from radiant.adapters.openai_compatible import parse_tutor_json


def test_parses_valid_json():
    result = parse_tutor_json('{"diagnosis":null,"action":"ask_clarification","explanation":"Need working","evidence":[]}')
    assert result.action == "ask_clarification"
    assert result.diagnosis is None


def test_rejects_non_json():
    with pytest.raises(ValueError, match="valid JSON"):
        parse_tutor_json("I think the learner made a mistake")


def test_rejects_diagnosis_on_abstention():
    with pytest.raises(ValueError, match="diagnosis=null"):
        parse_tutor_json('{"diagnosis":"guess","action":"abstain","evidence":[]}')
