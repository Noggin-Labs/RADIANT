import json

import pytest

from radiant.dataset import load_jsonl


def test_loads_pilot_dataset():
    rows = load_jsonl("data/pilot_scenarios.jsonl")
    assert len(rows) == 6
    assert rows[0].pair_id == "cf_same_answer_01"


def test_rejects_duplicate_ids(tmp_path):
    row = {
        "scenario_id": "same", "condition": "x", "problem": "1+1", "final_answer": "2",
        "student_work": "1+1=2", "reference_diagnosis": "correct", "expected_action": "diagnose"
    }
    path = tmp_path / "dup.jsonl"
    path.write_text(json.dumps(row) + "\n" + json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_jsonl(path)


def test_rejects_diagnosis_label_on_clarification(tmp_path):
    row = {
        "scenario_id": "bad", "condition": "x", "problem": "x+1=2", "final_answer": "1",
        "student_work": None, "reference_diagnosis": "guess", "expected_action": "ask_clarification"
    }
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps(row), encoding="utf-8")
    with pytest.raises(ValueError):
        load_jsonl(path)
