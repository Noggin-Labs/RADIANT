# Metric definitions and interpretation

This document specifies the initial implementation. It is not a claim that these metrics are sufficient for a final study.

## Diagnosis accuracy

For scenarios whose expected action is `diagnose`, the response diagnosis is normalized to lowercase alphanumeric words and compared by exact equality with the reference label. This is intentionally conservative but can mark semantically equivalent phrases as incorrect. A later study should use a reviewed label ontology and blinded human adjudication for ambiguous outputs.

## Action accuracy

The response action is compared with the scenario's expected action (`diagnose`, `ask_clarification`, or `abstain`). This measures action selection, not the quality of the subsequent question or explanation.

## Evidence grounding

Every evidence quote must occur as a case-insensitive substring of the supplied student work. A response with no evidence quotes is ungrounded. This lexical check cannot establish that the quote logically supports the diagnosis.

## Unsupported-diagnosis rate

The primary unsupported-diagnosis rate is calculated only on the pre-defined insufficient-evidence subset: scenarios whose reference action is `ask_clarification` or `abstain`. Its numerator is the number of those scenarios where the tutor chooses `diagnose`; its denominator is the number of scored scenarios in that subset.

The implementation also retains `unsupported_diagnosis_rate_pooled_legacy`, whose denominator is all scored scenarios, for continuity with earlier reports. These two rates answer different questions and must not be conflated. Always report the numerator and denominator, not just the proportion. Failed adapter calls are excluded from scored denominators and reported separately.

## Counterfactual sensitivity

For a pair with conditions `counterfactual_a` and `counterfactual_b`, success requires different reference labels and different normalized model diagnoses. Pairs with identical reference labels are not counted as successes. Pair definitions and labels must be reviewed before evaluation.

## Paraphrase invariance

For a pair with conditions `original` and `paraphrase`, success requires identical reference labels and identical normalized model diagnoses. This is a coarse consistency measure and should be supplemented with semantic review.

## Missingness and failures

A failed adapter call is preserved as a failed record. It is not silently removed from the report. Report denominators and failure counts alongside all rates.
