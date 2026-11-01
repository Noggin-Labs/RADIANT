import json

from radiant.adapters.scripted import ScriptedAdapter
from radiant.runner import run_evaluation


def test_runner_writes_report(tmp_path):
    report = run_evaluation("data/pilot_scenarios.jsonl", ScriptedAdapter(), tmp_path)
    assert report["metrics"]["n_scenarios"] == 6
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "records.csv").exists()
    saved = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert saved["adapter"] == "scripted-demo"
