# KAIROS benchmark v1

## Scope

This protocol evaluates regime-risk pseudo-label classification on the frozen
market-price file declared in `configs/benchmark-v1.json`. It supports a scoped
within-dataset comparison only. It does not establish causal identification,
physical validation, cross-domain generalization, or real-world early-warning
utility.

## Frozen design

- The input file and SHA-256 are fixed by configuration.
- KAIROS is imported from `src/kairos/model.py`; no experiment-local copy is
  permitted.
- KAIROS, GRU, and MLP receive identical input windows, temporal partitions,
  labels, optimizer family, epoch cap, patience, and five declared seeds.
- The target threshold is estimated from the training partition only.
- Samples whose forward target horizon crosses a partition boundary are
  excluded from that partition.
- Balanced accuracy is primary; F1 and ROC AUC are secondary.
- Every model/seed pair must produce one success or explicit failure record.
- Aggregation is forbidden unless every declared attempt is present exactly
  once and all reported values are finite.

## Admission boundary

A completed execution is technical evidence, not automatic claim admission.
Any public result must retain the pseudo-label, single-market-domain, temporal
split, seed, uncertainty, and comparator qualifiers above.
