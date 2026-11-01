# RADIANT Research Audit — v0.2

**Working paper title:** *Your LLM Is an Incompetent AI Tutoring System*
**Candidate scientific title:** *Do LLM Tutors Attend to Student Reasoning? A Counterfactual Evaluation of Evidence-Sensitive Mathematical Diagnosis*
**Status:** Research scoping only. No experiments have been run and no results are claimed.

## Executive decision

Do not build another broad benchmark of general tutoring competence. Existing work already covers pedagogical response quality, stepwise error verification, and end-to-end misconception diagnosis/remediation.

The strongest candidate contribution is a **controlled test of diagnostic evidence sensitivity**:

> When the mathematical problem and final answer are held constant, do tutoring LLMs use changes in the learner's intermediate reasoning to distinguish different underlying errors and produce correspondingly different feedback?

This is a candidate gap, not yet a novelty claim. A fuller review is required before preregistration.

## Literature and overlap audit

### 1. MRBench / Unifying AI Tutor Evaluation

Maurya et al. (NAACL 2025) introduce an eight-dimension taxonomy: mistake identification, mistake location, revealing of the answer, providing guidance, actionability, coherence, tutor tone, and humanlikeness. MRBench V1 contains 192 dialogues and 1,596 tutor responses; the official repository also lists V2 (200 dialogues, eight dimensions) and V3 (300 dialogues, with only four dimensions annotated for the additional examples).

**Implication:** RADIANT must not present a new generic tutoring-quality taxonomy as its contribution. Use the established dimensions as secondary response-quality measures where applicable.

Paper: https://aclanthology.org/2025.naacl-long.57/
Official data/code: https://github.com/kaushal0494/UnifyingAITutorEvaluation
Repository license: CC BY-SA 4.0. Check all upstream dataset licenses and attribution requirements before redistributing derivatives.

### 2. Stepwise Verification and Remediation

Daheim et al. (EMNLP 2024) collected 1,002 stepwise mathematical reasoning chains with teacher-annotated first error steps, evaluated verifiers, and showed that verification-grounded generation can improve targetedness and correctness of feedback.

**Implication:** Step-level error localization itself is not a new contribution. RADIANT would need to focus on a different property: sensitivity to controlled changes in evidence while holding other information fixed.

Paper: https://aclanthology.org/2024.emnlp-main.478/
Data and code: https://eth-lre.github.io/verify-then-generate/

### 3. MisconceptDialogue

Lee et al. (arXiv, 1 October 2026) evaluate five open-weight tutors in more than 5,000 simulated dialogues. They report a large scoring-method difference on identical dialogues (42.1% strict-match remediation versus 81.3% human-calibrated LLM-judge remediation), divergence between mistake detection and misconception diagnosis, and little evidence that tutors condition on supplied diagnosis labels under their tested prompt format. Their study explicitly scopes claims to simulated students and notes limitations around external validity and diagnosis-presentation format.

**Implication:** A new paper cannot claim that end-to-end diagnosis/remediation or diagnosis-label uptake has simply never been tested. It should investigate whether tutors attend to the *learner's worked evidence itself*, rather than merely whether they use an externally supplied diagnosis label. It must also report multiple scoring criteria and human anchoring where feasible.

Paper: https://arxiv.org/abs/2610.31679

### 4. MathDial

MathDial provides tutoring dialogues grounded in mathematical word problems and student confusions. The Hugging Face repository reports 2,899 rows (2,300 train; 599 test) and fields including problem, ground truth, incorrect solution, student profile, teacher-described confusion, and conversation.

**Implication:** Useful as a source for understanding existing scenario formats and as a possible comparison dataset. Do not assume its license from one mirror: the Hugging Face metadata and downstream MRBench licensing information need to be reconciled against the original source before copying or redistributing any records.

Dataset: https://huggingface.co/datasets/eth-nlped/mathdial
Original repository: https://github.com/eth-nlped/mathdial

### 5. Student-thinking inference from final answers

A 2026 study titled *Uncovering Student Thinking from Only the Answer: A GenAI Perspective* reports 55.25% alignment between a model's inferred student thinking and content-expert judgments in its College Algebra evaluation.

**Implication:** Answer-only diagnosis is already an active research topic. RADIANT should contrast answer-only input with worked-reasoning input, and test whether the system appropriately abstains when the answer alone underdetermines the learner's reasoning.

DOI: https://doi.org/10.31235/osf.io/3kaz2_v1

## Proposed research questions

- **RQ1 — Evidence sensitivity:** Does a tutor's diagnosis change appropriately when the learner's intermediate reasoning changes while the problem and final answer remain fixed?
- **RQ2 — Evidence grounding:** Does the tutor cite the specific step(s) that support its diagnosis, rather than merely naming a plausible misconception?
- **RQ3 — Surface robustness:** Does the diagnosis remain stable when the same reasoning is paraphrased without changing its mathematical content?
- **RQ4 — Uncertainty:** When only a final answer is supplied and multiple explanations remain plausible, does the tutor ask for working or clarification instead of inventing a diagnosis?
- **RQ5 — Pedagogical consequence:** Does a more accurate diagnosis lead to feedback that is more relevant, mathematically correct, and appropriately scaffolded?

## Candidate benchmark design

Use controlled, human-authored algebra scenarios. Each matched set should hold the problem and final answer constant while varying the intermediate reasoning in a mathematically meaningful way. Include:

1. Distinct error mechanisms that converge on the same final answer.
2. Correct reasoning and incorrect reasoning that share the same final answer, where such a pair can be constructed without contrivance.
3. Paraphrases that preserve the same reasoning and should preserve the diagnosis.
4. Answer-only cases where the correct response is calibrated uncertainty or a request for working.

Every item needs a worked mathematical validation, a reference diagnosis, a quoted evidence span, acceptable alternative diagnoses (if any), and a feedback rubric. Reject any item where the intended distinction is ambiguous or the arithmetic does not check out.

Start with a small pilot (approximately 12–15 matched sets). Expand only after the annotation guide and item validity survive independent review. Do not claim student learning gains from synthetic examples or model-simulated learners.

## Experimental conditions

For each selected model, keep model version, decoding settings, and scenario order controlled:

- **Answer-only:** problem plus final answer, without working.
- **Worked solution:** same problem and final answer plus the learner's intermediate steps.
- **Paraphrased worked solution:** mathematically equivalent rewording of the same steps.
- **Structured tutor prompt:** the worked-solution condition with explicit instructions to distinguish evidence, inference, and uncertainty.

A verifier-augmented condition can be added only after a transparent deterministic step-checker is implemented and independently tested. Do not use a model's self-reported chain-of-thought as ground truth.

## Primary outcomes

- Diagnosis accuracy against the reference annotation.
- Counterfactual diagnostic sensitivity: proportion of matched pairs where the diagnosis changes in the expected direction when the reasoning changes.
- Paraphrase invariance: proportion of paraphrase pairs retaining the same diagnosis.
- Unsupported-diagnosis rate on underdetermined answer-only cases.
- Evidence-grounding score: whether cited steps actually support the diagnosis.

Secondary outcomes can reuse relevant MRBench dimensions: guidance, actionability, answer revelation, coherence, and tutor tone. Report item-level results and uncertainty, not only one aggregate score.

## Scoring safeguards

- Use deterministic mathematical checks for each authored solution step wherever feasible.
- Have an independent adult mathematics reviewer check the pilot annotations before scaling.
- Blind evaluators to model identity and experimental condition.
- Do not rely on one LLM judge. If automated judges are used, report judge-family disagreement and compare a stratified subset with human ratings.
- Predefine how partial credit, multiple valid diagnoses, and abstention are scored.
- Keep diagnosis accuracy separate from feedback quality and actual learning outcomes.

## Noggimigo integration audit

The current `Noggin-Labs/noggimigo` repository already has a deterministic lesson runtime, mathematical answer verification, fixed misconception feedback keyed to normalized responses, a structured Hugging Face tutor adapter, pedagogical-output validation, BKT/MIRT-style answer-outcome tracking, and Brier/ECE/monotonicity metrics.

Important limitation: the current session API verifies submitted answers and uses lesson-defined misconception feedback; it is not yet a general free-form step-by-step misconception parser. Therefore Noggimigo should not be described as already solving RADIANT's target task. It may become a system-level comparator after an explicit, tested adapter is designed.

Repository: https://github.com/Noggin-Labs/noggimigo

## Model pilot candidates

- `Qwen/Qwen3-0.6B`: current Noggimigo default; Apache-2.0; useful for a low-resource baseline.
- `Qwen/Qwen2.5-Math-1.5B-Instruct`: math-oriented small model; Apache-2.0; useful as a second open-weight baseline.

These are candidate models, not a final model list. Hardware, runtime, and inference reproducibility must be checked before selecting the full panel.

Models: https://huggingface.co/Qwen/Qwen3-0.6B
https://huggingface.co/Qwen/Qwen2.5-Math-1.5B-Instruct

## Repository and service audit

- `Noggin-Labs/noggimigo` is accessible with write/admin permissions. No repository changes have been made.
- The repository contains both a Python `pyproject.toml` and a root Node workspace (`package.json`, `package-lock.json`) for `site/`; the npm lockfile is not a replacement for Python dependency locking.
- Hugging Face authentication is available for read operations. No model has been trained, uploaded, or deployed.
- SciSpace literature search is available and has been used for discovery.
- Canva contains an 11-page science-research presentation template with placeholder text. It has not been edited.
- Gmail was not searched because no email task is currently necessary.

## Immediate next steps

1. Read the full MRBench, MisconceptDialogue, and Stepwise Verification methods and appendices.
2. Resolve upstream dataset licenses before reusing any third-party examples.
3. Write the annotation guide and scenario schema.
4. Construct and mathematically verify the first 12–15 matched sets.
5. Run a small pilot on the two candidate open-weight models.
6. Revise the protocol and preregister before any full evaluation.

**No results, novelty claims, or student-learning claims are established by this audit.**
