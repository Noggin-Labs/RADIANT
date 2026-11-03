# Independent review of `data/pilot_benchmark_v1.jsonl`

**Reviewer:** phase-2 audit. **Scope:** mathematical correctness, reference-label defensibility, pair validity, evidence traceability.
**Method:** every algebraic chain recomputed by hand and checked for internal consistency; conditional probes executed via `scripts/adversarial_metric_probes.py`.

## 1. Summary

12 matched sets, 21 scenarios. Structural validation passes (9 matched sets: 5 counterfactual + 4 paraphrase; 3 unpaired insufficient-evidence singletons; 0 structural issues).

**One scenario was logically ambiguous and has been revised** (`cf_inverse_op_b`). Everything else was verified as stated.

## 2. Per-set verification

| Set | Problem | Check | Verdict |
|---|---|---|---|
| `cf_add_instead_of_subtract` | `2x+3=11` | A: `2x=8 → x=4` ✓. B: `2x=14` is wrong (should be 8); `x=7` follows consistently from 14; stated answer 4 contradicts it ✓ | Sound |
| `cf_misdistribution` | `3(x−2)=12` | A: `3x−6=12 → 3x=18 → x=6` ✓. B: `3x−2=12 → 3x=14 → x=14/3`; stated 6 contradicts ✓ | Sound |
| `cf_sign_on_division` | `−2x=8` | A: `x=8/(−2)=−4` ✓. B: dropping the minus gives `2x=8 → x=4`; stated −4 contradicts ✓ | Sound |
| `cf_wrong_inverse_operation` | `x/4=3` | A: multiply by 4 → `x=12` ✓. B: **was ambiguous** — dividing both sides by 4 is itself *valid* (`x/16=3/4 → x=12`), so labelling the operation "invalid" depended on an unstated reading. **Revised**: B now explicitly drops the 16 (`x/16=3/4` → wrote `x=3/4`), which is unambiguously invalid | **Revised** |
| `cf_arithmetic_slip` | `23×4` | A: `80+12=92` ✓. B: `3×4=9` is false, `80+9=89`, stated 92 ✓. Correctly labelled `arithmetic_error`, not conceptual | Sound |
| `para_distribution_ward` | `4(x+5)=36` | `4x+20=36 → 4x=16 → x=4` ✓; paraphrase states the same two operations | Sound |
| `para_fraction_ward` | `x/5+2=5` | `x/5=3 → x=15` ✓; paraphrase identical | Sound |
| `para_compensation_ward` | `47+38` | `47+40−2=85` ✓; paraphrase says add 40 then take back 2 | Sound |
| `para_linear_ward` | `5x−7=18` | `5x=25 → x=5` ✓; paraphrase identical | Sound |
| `under_answer_only_clarify` | `2x=10`, answer 5, no working | Correct answer, method unknown; `ask_clarification` (scenario validation forbids work on clarification cases) | Sound |
| `under_answer_only_abstain` | `x+5=12`, answer 7, no working | Same, `abstain` | Sound |
| `under_restated_answer` | `3x=12`, work "x = 4" | Work restates the answer with no operation, so no reasoning is evidenced | Sound |

## 3. Consistency properties verified

- Every counterfactual set holds **the stated final answer constant** while changing the reasoning. This is the property the sensitivity metric depends on, and it is what makes "same answer, different reasoning" meaningful.
- In every counterfactual B, the stated final answer **contradicts the shown work**. That is deliberate: it is precisely the case a final-answer-only evaluator cannot detect.
- No scenario labels a learner trait. Labels describe the work (`invalid_intermediate_operation`, `arithmetic_error`, `correct_reasoning`).
- Evidence steps are substrings of the corresponding `student_work` where present, so the lexical grounding check can succeed legitimately.

## 4. Metric behaviour on this benchmark

`scripts/adversarial_metric_probes.py` → **10/10 probes behaved as required**, including:

- two different wrong labels → sensitivity **0/0 excluded**, not a success;
- two missing diagnoses → invariance **not** counted as success;
- duplicate condition → pair marked invalid, excluded from the denominator;
- failed call inside a pair → pair invalidated;
- legitimate pair → still scores success (no over-blocking).

## 5. Remaining weaknesses

1. **No independent human review.** The sets were authored by the same process that wrote the metrics. `docs/ANNOTATION_GUIDE.md` requires two blind reviewers; none have been recorded. This benchmark is therefore **not** yet a validated instrument.
2. **21 scenarios cannot support inference.** Wilson intervals are descriptive only.
3. **Narrow topic coverage** — linear equations, one distribution case, one arithmetic slip, one fraction division. No negative-number, unit-conversion or multi-step word problems.
4. **Labels are exact strings.** "Invalid operation" and "invalid_intermediate_operation" score as different. Documented, conservative, but it limits cross-model comparability.
5. **Evidence grounding is lexical.** A scenario's `evidence_steps` are guaranteed present, which makes grounding easy to satisfy without demonstrating logical support.

## 6. Recommendation

Hold the benchmark at 12 sets until two independent educators have labelled all sets blind. Expanding an unreviewed benchmark increases apparent size without increasing validity.
