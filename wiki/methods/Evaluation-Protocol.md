---
title: Evaluation Protocol
status: VALIDATED
last_updated: 2026-08-19
paper_source: false
---

# Evaluation Protocol

## Current status

Benchmark v1 has a frozen protocol, configuration, dataset checksum, temporal
split, target threshold rule, matched seed registry, comparator set, metrics,
failure accounting, and admission boundary. [Trace: `C-EXP-001`, `C-EXP-002`,
`C-DATA-002` → `E-EXP-001`, `E-DATA-001`]

## Required declaration

Each future protocol must predeclare the model identity, data release, temporal
splits, label and lead-time estimands, smoothing and thresholds, comparator
implementations, hyperparameter budget, seeds, uncertainty unit, exclusions,
failure handling, and acceptance gates.

All models must receive matched information and disclosed tuning budgets.
Results must report complete denominators and per-seed records. Intervention
subsets and cross-domain tracks are secondary analyses unless separately
preregistered. A completed run cannot change metric or claim wording by itself.

## Benchmark-v1 boundary

<!-- trace: C-EXP-002 C-DATA-002 C-PERF-001 E-EXP-001 E-DATA-001 -->

The active runner uses the canonical eight-feature KAIROS implementation and
the same five seeds for KAIROS, GRU, and MLP. Its target is a training-derived
pseudo-label on one frozen market dataset. Completion can support only a scoped
within-dataset comparison; it cannot support causal, cross-domain, or external
early-warning language.
