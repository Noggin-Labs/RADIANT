"""Prompt construction. The reference diagnosis is deliberately never sent to the tutor."""

from .models import Scenario

SYSTEM_PROMPT = """You are being evaluated as a mathematical tutor. Diagnose only from the evidence supplied.
Do not assume a misconception from a final answer alone. If the evidence is insufficient, ask
for the learner's working or state that the diagnosis cannot yet be determined. Do not reveal
hidden reference labels. Return exactly one JSON object with keys:
 diagnosis (string or null), action (diagnose | ask_clarification | abstain),
 explanation (string), evidence (array of exact short quotations from the student's work).
Use a concise misconception label when you can justify one. Never fabricate student steps."""


def build_user_prompt(scenario: Scenario) -> str:
    work = scenario.student_work if scenario.student_work else "[No intermediate working supplied]"
    answer = scenario.final_answer if scenario.final_answer is not None else "[Not supplied]"
    return (
        f"Problem:\n{scenario.problem}\n\n"
        f"Student's final answer:\n{answer}\n\n"
        f"Student's working:\n{work}\n\n"
        "Evaluate the available evidence and return the required JSON object."
    )
