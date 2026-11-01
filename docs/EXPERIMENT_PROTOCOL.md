# RADIANT: Initial experiment protocol (draft)

## Status

Protocol draft only. Do not describe the design as preregistered or validated.

## Target construct

Evidence-sensitive mathematical diagnosis: the extent to which a tutor's diagnosis is appropriately determined by the learner's intermediate mathematical work, including recognition of insufficient evidence.

## Experimental units

A scenario is one problem + final answer + optional student work. A matched set contains scenarios designed to isolate a single evidence change (for example, a changed reasoning path with the same problem and final answer).

## Conditions

- `answer_only`: problem and final answer; no working.
- `original`: canonical student working.
- `paraphrase`: semantically equivalent working with changed wording.
- `counterfactual_a` / `counterfactual_b`: same problem and final answer, distinct reasoning paths and reference diagnoses.
- `underdetermined`: intentionally insufficient evidence; expected action is clarification or abstention.

## Primary outcomes

1. Diagnosis accuracy on diagnosis-eligible cases.
2. Counterfactual sensitivity on pre-specified matched pairs.
3. Paraphrase invariance on pre-specified matched pairs.
4. Unsupported-diagnosis rate on underdetermined cases.

## Secondary outcomes

- Evidence quotation validity.
- Action selection accuracy.
- Feedback correctness and pedagogical quality, scored in a separate annotation pass.

## Annotation

At least two independent reviewers should inspect each mathematical scenario and its reference diagnosis. Disagreements should be adjudicated and documented. Reviewers should not see model identities or outputs while creating gold labels.

## Exclusions and failures

Predefine malformed model output, API failures, ambiguous labels, and invalid scenarios. Preserve failure counts in reports. Do not silently exclude cases after inspecting model performance.

## Reproducibility record

Record dataset version/hash, scenario count, code commit, Python version, provider, model identifier, prompt version/hash, generation settings, run timestamp, and retry policy.

## Limitations

Synthetic scenarios test controlled behaviour, not authentic learner cognition. A model may quote evidence without understanding it. Exact string matching is a coarse proxy for diagnosis correctness. No inference about actual learning gains follows from these metrics.
