# RADIANT
### Reasoning Analysis and Diagnostic Investigation for Advanced Neural-informed Tutoring

**A research initiative by [Noggin Labs](https://github.com/Noggin-Labs)** and [**Folarera Kassim**](https://github.com/FolatheDuckofDuckingburg)

> Investigating whether large language model tutors can understand, diagnose, and respond to the reasoning behind a student's answer.

---

## Overview

RADIANT is a research project investigating the diagnostic capabilities of large language models (LLMs) in mathematical tutoring.

A tutoring system should do more than determine whether an answer is correct. It should be able to examine the reasoning that produced that answer, identify misconceptions, distinguish between different reasoning errors, and provide feedback grounded in the learner's actual work.

However, a correct or incorrect final answer does not necessarily reveal how a student arrived at it.

RADIANT investigates this problem through controlled evaluations of LLM tutoring systems, focusing on their ability to interpret intermediate mathematical reasoning rather than relying exclusively on final answers.

## Research question

**Do LLM tutors genuinely use student reasoning when diagnosing mathematical misconceptions, or do they primarily rely on surface-level answer patterns?**

### Research objectives

- Evaluate the accuracy of mathematical misconception diagnosis.
- Investigate whether different reasoning paths leading to the same answer produce appropriately different diagnoses.
- Test whether paraphrasing student reasoning changes diagnostic conclusions unnecessarily.
- Measure how frequently tutors make unsupported assumptions when insufficient information is available.
- Evaluate whether accurate diagnoses lead to relevant, mathematically correct, and appropriately scaffolded feedback.

## Proposed research questions

| ID | Research question |
|---|---|
| RQ1 | Do tutors respond appropriately to changes in intermediate reasoning when the final answer remains constant? |
| RQ2 | Can tutors identify and reference the specific steps supporting their diagnoses? |
| RQ3 | Are diagnoses stable when mathematically equivalent reasoning is paraphrased? |
| RQ4 | Do tutors recognise when the available evidence is insufficient? |
| RQ5 | Does diagnostic accuracy translate into better-targeted instructional feedback? |

## Methodology

The initial investigation will use controlled mathematical scenarios, beginning with algebra.

Proposed experimental conditions include:

1. **Answer-only:** The tutor receives the problem and final answer.
2. **Worked reasoning:** The tutor receives the student's intermediate steps.
3. **Paraphrased reasoning:** The tutor receives equivalent reasoning expressed differently.
4. **Underdetermined evidence:** The tutor receives insufficient information to establish a reliable diagnosis.

Matched scenarios will help isolate the influence of intermediate reasoning on diagnostic behaviour.

### Evaluation metrics

| Metric | What it measures |
|---|---|
| Diagnosis accuracy | Whether the identified misconception is correct |
| Diagnostic sensitivity | Whether diagnoses respond appropriately to changed reasoning |
| Paraphrase invariance | Whether equivalent reasoning preserves the diagnosis |
| Unsupported-diagnosis rate | How often tutors assert diagnoses without sufficient evidence |
| Evidence grounding | Whether diagnoses reference relevant mathematical steps |
| Feedback quality | Whether instructional feedback is correct and appropriately targeted |

Mathematical correctness, diagnostic accuracy, and instructional quality will be evaluated separately.

## Research foundations

RADIANT builds upon existing research in AI tutoring and mathematical reasoning evaluation.

Relevant work includes:

- [Unifying AI Tutor Evaluation — MRBench (NAACL 2025)](https://aclanthology.org/2025.naacl-long.57/)
- [Stepwise Verification and Remediation of Student Reasoning Errors (EMNLP 2024)](https://aclanthology.org/2024.emnlp-main.478/)
- [MisconceptDialogue (2026)](https://arxiv.org/abs/2610.31679)
- [MathDial](https://github.com/eth-nlped/mathdial)

These studies provide important foundations for evaluating tutoring quality, reasoning-error identification, and misconception diagnosis.

RADIANT aims to investigate a complementary question: how reliably do tutors use changes in the learner's actual reasoning as diagnostic evidence?

This is a research hypothesis, not an established novelty claim.

## Relationship with Noggimigo

RADIANT is a research initiative within **Noggin Labs**.

Its findings may inform the development of [Noggimigo](https://github.com/Noggin-Labs/noggimigo), an open-source tutoring system focused on structured, adaptive learning.

The projects have distinct responsibilities:

- **RADIANT:** Researches and evaluates diagnostic behaviour in LLM tutors.
- **Noggimigo:** Develops tutoring infrastructure and learner-facing educational functionality.

Research findings will only be incorporated into Noggimigo when supported by appropriate evidence and testing.

## Current status

**Research stage: Protocol development and literature review.**

| Component | Status |
|---|---|
| Initial research question | Defined |
| Literature review | Underway |
| Research objectives | Drafted |
| Evaluation methodology | Proposed |
| Scenario dataset | Not yet validated |
| Pilot evaluation | Not yet conducted |
| Experimental results | Not yet available |

No claims of demonstrated learning improvement or diagnostic superiority are currently made.

## Research principles

RADIANT follows several principles:

- **Evidence over assumptions:** A tutor should not invent a misconception from insufficient information.
- **Mathematical correctness:** Diagnoses and explanations must be mathematically defensible.
- **Reproducibility:** Evaluation conditions and scoring criteria should be documented.
- **Separation of outcomes:** Correct diagnosis does not automatically imply effective teaching.
- **Scientific caution:** Hypotheses must remain distinct from experimental findings.

## Organisation

**Noggin Labs**

RADIANT is an independent research initiative within Noggin Labs, focused on the evaluation of reasoning-aware AI tutoring.

---

*RADIANT — Understanding the reasoning behind the answer.*
