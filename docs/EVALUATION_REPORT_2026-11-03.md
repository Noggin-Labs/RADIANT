# RADIANT evaluation report — 2026-11-03

**Repository:** `Noggin-Labs/RADIANT`, commit `d3e6df4`.
**Environment:** Python 3.12.3, NumPy 2.5.4, pandas 3.1.0, SciPy 1.18.1, pytest.
**Test status:** `pytest -q` → **25 passed** (10 pre-existing + 15 new regression tests).

---

## 1. Metric audit — defects found and corrected

Each item was a genuine validity failure, not a style issue. Every correction has a regression test in `tests/test_metrics_regressions.py`.

| # | Defect | Why it was wrong | Correction |
|---|---|---|---|
| 1 | Counterfactual sensitivity counted *any* two different outputs as success | A tutor emitting two different **wrong** labels looked "sensitive to reasoning"; it is merely noisy | Success now requires both diagnoses present, **each correct against its own reference**, and different |
| 2 | Paraphrase invariance counted two **missing** diagnoses as agreement | `normalize(None) == normalize(None)` is `True`, so two silent failures scored as perfect invariance | Success now requires both diagnoses present and correct as well as equal |
| 3 | Pairs were never checked for structural equivalence | A "paraphrase" pair with different reference labels, or a "counterfactual" pair with different final answers, was silently treated as a valid pair | `validate_pairs()` checks problem identity, final-answer identity (counterfactual), reference-label difference (counterfactual) / identity (paraphrase), and that the work actually differs |
| 4 | Duplicate conditions were silently collapsed | `{r.condition: r for r in group}` kept the **last** record and discarded the rest without a trace | Duplicates are detected and the pair is marked invalid; it is excluded from the rate and listed in `invalid_pairs` |
| 5 | Unsupported-diagnosis rate used *all* scenarios as its denominator | The metric answered "how often does the tutor over-diagnose, out of everything" rather than "out of the cases where a diagnosis is unjustified" | Primary rate now uses the insufficient-evidence subset (`ask_clarification`/`abstain`); the pooled rate is retained under an explicit `_pooled_legacy` name |
| 6 | Lexical substring matching risked being read as entailment | A quote can be present verbatim and still not support the diagnosis | Field and docs now state it is a lexical presence check only, with `evidence_grounding_note` emitted in every report; both a supporting and a fabricated quote are tested |
| 7 | Failed adapter calls were scored as **wrong answers** | `diagnosis_correct=False` on a timeout deflated accuracy by an amount proportional to infrastructure flakiness | Failures now carry `diagnosis_correct=None`, are excluded from accuracy denominators, appear in `n_failures`/`failure_rate`/`failed_scenario_ids`, and invalidate the pairs they belong to |
| 8 | Exact string matching could be mistaken for semantic correctness | Two wordings of the same misconception score as incorrect | Retained (conservative) but documented in `diagnosis_accuracy_note`; a test asserts the behaviour *and* the emitted caveat |

Additionally, every rate now reports `{rate, numerator, denominator, wilson_95ci}`, so no rate can be read against the wrong base. The interval is descriptive only: pilot scenarios are a convenience sample, not a random sample from a defined population.

**Note on one interface change:** `diagnosis_accuracy` and the other rates changed from a bare float to a dict. One pre-existing test asserted `is None`; it was updated to assert `rate is None` **and** `denominator == 0`, preserving its original intent (an empty accuracy must not read as zero) while adopting the new shape required for explicit denominators.

## 2. Reviewed pilot benchmark

`data/pilot_benchmark_v1.jsonl` — **12 matched sets, 21 scenarios**, all independent-checkable arithmetic/algebra:

- 5 counterfactual sets (`cf_*`), 4 paraphrase sets (`para_*`), 3 insufficient-evidence singletons (`under_*`).
- Every counterfactual set holds the **stated final answer constant** while changing the reasoning, which is the only way the test means anything.
- Each scenario carries `reference_diagnosis`, `evidence_steps`, `pair_id`, and a note explaining the rationale.
- Labels describe the *work* (`invalid_intermediate_operation`, `arithmetic_error`), never the learner. No diagnosis of ability, attention, motivation or neurodevelopmental status appears anywhere.

Structural validation on load: `valid=True`, 9 matched sets, **0 issues**, 3 unpaired singletons.

Examples of the reasoning actually encoded:

| Set | Condition A | Condition B |
|---|---|---|
| `cf_add_instead_of_subtract` | `2x+3=11 → 2x=8 → x=4` (correct) | `2x+3=11 → 2x=14 → x=7`, then "I wrote x = 4" (invalid operation; same stated answer) |
| `cf_arithmetic_slip` | `20×4=80; 3×4=12; 92` (correct) | `20×4=80; 3×4=9; 89`, then "I wrote 92" (arithmetic slip, valid method) |
| `para_compensation_ward` | `47+38 = 47+40−2 = 87−2 = 85` | "I rounded 38 up to 40 … then took back the 2" |

**All 12 sets require independent human mathematics review before research use.** They were authored by the same process that audited the metrics, so they are not independent of it. `docs/ANNOTATION_GUIDE.md` specifies two-reviewer independent labelling with adjudication; no second reviewer has yet been recorded.

## 3. Model evaluation — BLOCKED, not performed

**No Hugging Face inference was available in this environment, so no model was evaluated. No model performance numbers are reported, because reporting them would require inventing them.**

Specifically not done:

- Qwen3-0.6B — not run; licence and revision not verified.
- Qwen2.5-Math-1.5B-Instruct — not run; licence and revision not verified.
- No `transformers`/`torch` inference stack was installed, no weights were downloaded, and no GPU/CPU generation was executed.

What *was* run is a **plumbing check only**, using `ScriptedAdapter`, which reads the reference label directly and is therefore an oracle:

| Quantity | Oracle result | Interpretation |
|---|---|---|
| Scenarios | 21 | — |
| Failures | 0 | — |
| Action accuracy | 21/21 | **Oracle. Meaningless as model performance.** |
| Diagnosis accuracy | 18/18 | **Oracle.** |
| Unsupported diagnosis (insufficient evidence) | 0/3 | **Oracle.** |
| Evidence grounding | 18/18 | **Oracle.** |
| Counterfactual sensitivity | 5/5 | **Oracle.** |
| Paraphrase invariance | 4/4 | **Oracle.** |

The value of this run is that the pipeline, the pair logic, the denominators and the report writer all work end-to-end. Per the adapter's own docstring, these numbers must never be cited as model performance.

### Exact procedure once HF inference is available

```bash
pip install -e ".[dev]" transformers torch accelerate
# 1. Verify the licence and pin the revision for each candidate model.
# 2. Record the exact commit SHA of each model repo, not just the name.
python -c "from radiant.cli import main; main()" --help
# 3. Run every model against the identical dataset and identical prompt.
#    SYSTEM_PROMPT is hashed into the report as prompt_sha256.
# 4. Preserve raw outputs: report.json keeps every response and every error.
```

Report, per model: action accuracy, diagnosis accuracy, reasoning-evidence sensitivity (both-correct counterfactuals only), paraphrase consistency, unsupported-inference rate on the insufficient-evidence subset, evidence-grounding rate, missing-output rate, runtime, and peak memory — each with its denominator and interval. Fix `do_sample=False` and a seed so runs are reproducible.

## 4. What the framework can and cannot support

**Can support:** a descriptive, auditable comparison of how different tutors respond to matched reasoning variation on a small, human-reviewable benchmark.

**Cannot support:** any claim of improved student learning, any claim that the benchmark is a validated educational assessment, any diagnosis of a learner, or any population-level inference from 21 scenarios.

## 5. Next validation study (proposed)

1. Two independent mathematics educators label all 12 sets blind; report agreement and adjudicate disagreements.
2. Expand to ~40 sets covering fractions, negative numbers, distribution, and unit conversion — each with a reviewer-signed rationale.
3. Run 2–3 small licensed models plus a no-model baseline, with pinned revisions.
4. Only then consider whether the counterfactual-sensitivity metric predicts anything about real tutoring transcripts.
