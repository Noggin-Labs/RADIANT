# RADIANT

### Reasoning Analysis and Diagnostic Investigation for Advanced Neural-informed Tutoring

**A research initiative by [Noggin Labs](https://github.com/Noggin-Labs).**

RADIANT is an experimental evaluation framework for investigating whether large language model (LLM) tutors use students' intermediate mathematical reasoning as evidence when diagnosing misconceptions.

> **Core question:** When two learners give the same final answer using different reasoning, does an LLM tutor diagnose them differently for the right reasons?

RADIANT is a research evaluation project, not a learner-facing tutor. It does not currently establish that any model improves learning outcomes.

## Research aims

- Measure mathematical diagnosis accuracy against human-reviewed reference labels.
- Test counterfactual diagnostic sensitivity: different reasoning paths with the same final answer should lead to appropriately different diagnoses.
- Test paraphrase invariance: equivalent reasoning expressed differently should not cause arbitrary diagnosis changes.
- Measure unsupported diagnoses when only a final answer is available.
- Assess whether tutor explanations cite actual evidence from the student's work.

## Repository structure

```text
RADIANT/
├── .github/workflows/tests.yml
├── data/
│   └── pilot_scenarios.jsonl
├── docs/
│   ├── research_audit.md
│   └── scenario_schema_draft.json
├── src/radiant/
│   ├── adapters/
│   │   ├── base.py
│   │   ├── openai_compatible.py
│   │   └── scripted.py
│   ├── analysis.py
│   ├── cli.py
│   ├── dataset.py
│   ├── models.py
│   ├── prompting.py
│   ├── runner.py
│   └── scoring.py
├── tests/
├── .env.example
├── LICENSE
└── pyproject.toml
```

## Quick start

Requires Python 3.10 or newer.

```bash
# Create and activate a virtual environment (Windows PowerShell)
py -m venv .venv
.venv\\Scripts\\Activate.ps1

# Install the package and test dependencies
python -m pip install -e ".[test]"

# Validate the example scenarios
radiant validate data/pilot_scenarios.jsonl

# Run a pipeline smoke test
radiant evaluate data/pilot_scenarios.jsonl --adapter scripted --output results/demo

# Run tests
pytest
```

The scripted adapter is an oracle-backed test fixture. It reads reference labels to verify that the pipeline works. **Its scores are not model results and must never be reported as experimental findings.**

## Evaluate an actual model

Install the optional API dependency:

```bash
python -m pip install -e ".[api]"
```

Set environment variables (do not commit API keys):

```bash
# PowerShell example
$env:RADIANT_API_BASE = "https://api.openai.com/v1"
$env:RADIANT_API_KEY = "YOUR_KEY"
$env:RADIANT_MODEL = "YOUR_MODEL_ID"
```

Then use the adapter in Python:

```python
from radiant.adapters.openai_compatible import OpenAICompatibleAdapter
from radiant.runner import run_evaluation

adapter = OpenAICompatibleAdapter()
report = run_evaluation(
    "data/pilot_scenarios.jsonl",
    adapter,
    "results/model_run",
)
print(report["metrics"])
```

The adapter sends the problem, final answer, and student working to the model. It does **not** send reference diagnoses or gold evidence labels.

## Scenario format

Each line in the dataset is a JSON object. Core fields:

| Field | Meaning |
|---|---|
| `scenario_id` | Unique scenario identifier |
| `condition` | Experimental condition name |
| `problem` | Mathematical task |
| `final_answer` | Learner's submitted answer, if available |
| `student_work` | Learner's intermediate reasoning, if available |
| `reference_diagnosis` | Human-reviewed label; null when diagnosis is not justified |
| `evidence_steps` | Reference evidence snippets |
| `expected_action` | `diagnose`, `ask_clarification`, or `abstain` |
| `pair_id` | Optional matched-pair identifier |

Reference labels must be prepared independently and hidden from the model adapter. The included cases are synthetic software fixtures, not a validated educational assessment dataset.

## Metrics

The first implementation reports:

- **Diagnosis accuracy:** exact normalized match to the reference label on diagnosis-eligible cases.
- **Action accuracy:** whether the model chose the expected action.
- **Evidence-grounding rate:** whether cited evidence snippets occur verbatim in the supplied student work.
- **Unsupported-diagnosis rate:** frequency of diagnosing scenarios whose reference action is clarification or abstention.
- **Counterfactual sensitivity:** whether paired scenarios with distinct reference diagnoses receive distinct model diagnoses.
- **Paraphrase invariance:** whether paired paraphrases with the same reference diagnosis receive the same model diagnosis.

These are deliberately simple initial metrics. Exact-match labels can penalize semantically equivalent diagnoses; evidence quotation is not proof that the model reasoned correctly; pair-level rates are only meaningful for carefully constructed, reviewed pairs. Human annotation and calibration are required before substantive claims.

## Experimental safeguards

1. Freeze scenario definitions and scoring rules before the main evaluation.
2. Have mathematical scenarios and reference labels independently reviewed.
3. Keep gold labels out of model prompts and logs sent to the model.
4. Record model ID, provider, prompt version, temperature, date, and dataset hash for each run.
5. Separate diagnosis quality from feedback quality and actual learner outcomes.
6. Report failures, abstentions, missing outputs, and uncertainty rather than silently dropping them.
7. Do not treat synthetic learner scenarios as evidence of real-world learning gains.

## Relationship to Noggimigo

RADIANT is a research initiative within Noggin Labs. Noggimigo is a separate tutoring-engine project. RADIANT's findings may inform Noggimigo only after independent evaluation and review; this repository does not depend on Noggimigo internals.

## Research status

**Early prototype — protocol and evaluation infrastructure under development.** The example dataset is a software fixture. It has not been independently validated, and no model comparison or learning-outcome claim is made by this repository.

See [`docs/research_audit.md`](docs/research_audit.md) for the current literature-overlap review and proposed research design.

## License

MIT. See [LICENSE](LICENSE).

## Run an API-backed evaluation from the CLI

After setting the environment variables above:

```bash
radiant evaluate data/pilot_scenarios.jsonl --adapter openai-compatible --output results/model_run
```

Each run writes `report.json` and `records.csv`. The JSON report includes the dataset SHA-256, prompt SHA-256, software/Python versions, UTC timestamp, adapter/model identifier, failure count, aggregate metrics, paired diagnostics, and per-scenario records. Store the exact code revision and provider settings with any research release.

Metric definitions and caveats are documented in [`docs/METRICS.md`](docs/METRICS.md).
