"""Experiment orchestration and result serialization."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from radiant import __version__
from radiant.prompting import SYSTEM_PROMPT

from .analysis import paired_diagnostics
from .adapters.base import TutorAdapter
from .models import EvaluationRecord
from .scoring import aggregate_metrics, score_response
from .dataset import load_jsonl


def run_evaluation(dataset_path: str | Path, adapter: TutorAdapter, output_dir: str | Path) -> dict:
    scenarios = load_jsonl(dataset_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records: list[EvaluationRecord] = []

    for scenario in scenarios:
        try:
            response = adapter.respond(scenario)
            records.append(score_response(scenario, response))
        except Exception as exc:  # preserve failures as explicit records
            from .models import TutorResponse
            records.append(EvaluationRecord(
                scenario_id=scenario.scenario_id,
                condition=scenario.condition,
                pair_id=scenario.pair_id,
                reference_diagnosis=scenario.reference_diagnosis,
                response=TutorResponse(diagnosis=None, action="error", explanation="Adapter failure"),
                diagnosis_correct=False if scenario.expected_action == "diagnose" else None,
                action_correct=False,
                evidence_grounded=None,
                unsupported_diagnosis=False,
                error=f"{type(exc).__name__}: {exc}",
            ))

    record_dicts = [record.to_dict() for record in records]
    metrics = aggregate_metrics(records)
    dataset_bytes = Path(dataset_path).read_bytes()
    report = {
        "project": "RADIANT",
        "software_version": __version__,
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "adapter": adapter.name,
        "model": getattr(adapter, "model", None),
        "prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest(),
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "n_failures": sum(record.error is not None for record in records),
        "dataset": str(dataset_path),
        "metrics": metrics,
        "paired_diagnostics": paired_diagnostics(records),
        "records": record_dicts,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if record_dicts:
        with (output / "records.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(record_dicts[0].keys()))
            writer.writeheader()
            writer.writerows(record_dicts)
    return report
