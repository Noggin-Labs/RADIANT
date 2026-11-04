"""Typed domain models used by the RADIANT evaluation pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    condition: str
    problem: str
    final_answer: str | None
    student_work: str | None
    reference_diagnosis: str | None
    evidence_steps: tuple[str, ...] = ()
    expected_action: str = "diagnose"
    pair_id: str | None = None
    notes: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Scenario":
        required = ("scenario_id", "condition", "problem", "expected_action")
        missing = [key for key in required if key not in raw]
        if missing:
            raise ValueError(f"Scenario missing required fields: {', '.join(missing)}")
        return cls(
            scenario_id=str(raw["scenario_id"]),
            condition=str(raw["condition"]),
            problem=str(raw["problem"]),
            final_answer=raw.get("final_answer"),
            student_work=raw.get("student_work"),
            reference_diagnosis=raw.get("reference_diagnosis"),
            evidence_steps=tuple(raw.get("evidence_steps", ())),
            expected_action=str(raw["expected_action"]),
            pair_id=raw.get("pair_id"),
            notes=str(raw.get("notes", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["evidence_steps"] = list(self.evidence_steps)
        return result


@dataclass(frozen=True)
class TutorResponse:
    diagnosis: str | None
    action: str
    explanation: str = ""
    evidence: tuple[str, ...] = ()
    raw_text: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any], raw_text: str = "") -> "TutorResponse":
        return cls(
            diagnosis=raw.get("diagnosis"),
            action=str(raw.get("action", "diagnose")),
            explanation=str(raw.get("explanation", "")),
            evidence=tuple(str(x) for x in raw.get("evidence", [])),
            raw_text=raw_text,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnosis": self.diagnosis,
            "action": self.action,
            "explanation": self.explanation,
            "evidence": list(self.evidence),
            "raw_text": self.raw_text,
        }


@dataclass
class EvaluationRecord:
    scenario_id: str
    condition: str
    pair_id: str | None
    reference_diagnosis: str | None
    response: TutorResponse
    diagnosis_correct: bool | None
    action_correct: bool
    evidence_grounded: bool | None
    unsupported_diagnosis: bool
    error: str | None = None
    # Carried on the record so that aggregation and pair validation do not need
    # the source Scenario objects, and so reports stay self-describing.
    expected_action: str = "diagnose"
    problem: str | None = None
    final_answer: str | None = None
    student_work: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "condition": self.condition,
            "pair_id": self.pair_id,
            "reference_diagnosis": self.reference_diagnosis,
            **self.response.to_dict(),
            "diagnosis_correct": self.diagnosis_correct,
            "action_correct": self.action_correct,
            "evidence_grounded": self.evidence_grounded,
            "unsupported_diagnosis": self.unsupported_diagnosis,
            "error": self.error,
            "expected_action": self.expected_action,
            "problem": self.problem,
            "final_answer": self.final_answer,
            "student_work": self.student_work,
        }
