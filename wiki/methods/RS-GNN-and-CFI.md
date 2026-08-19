---
title: RS-GNN and CFI
status: PROPOSED
last_updated: 2026-08-19
paper_source: false
---

# RS-GNN and CFI

## Canonical boundary

<!-- trace: C-IMPL-001 C-IMPL-002 E-IMPL-001 -->

The canonical code is `src/kairos/model.py`. At an implementation-inventory
level it contains four named stages:

1. RSE encodes edge features with learned gating.
2. CSM assigns each edge probabilities over five lifecycle states.
3. RMP/TIP aggregates edge messages and applies an information bottleneck.
4. SCP maps learned representations to a regime prediction.

The generated CFI and counterfactual outputs are model-internal scores and
attributions. Until a causal design is admitted, they must not be described as
identified real-world causes or intervention effects.

## Static defaults and data construction

<!-- trace: C-IMPL-002 E-IMPL-001 -->

The module declares 28 unique tickers in seven risk-on clusters and five
risk-off clusters, yielding 35 directed cluster pairs. It builds eight edge channels: flow, acceleration,
magnitude, a median-price proxy ratio, rolling correlation, correlation change,
spread, and volatility ratio. Default sequence length is 20; hidden width is
48; bottleneck width is 24; seed is 42. These are code defaults, not approved
protocol values.

The pseudo-target marks a bearish outcome from a future drop over a 15-step
lookahead, starting from threshold 0.7 and potentially raising it to the 75th
percentile of positive drops. This is a model-development pseudo-label, not a
causal, economic, or clinical ground truth. [Trace: `C-IMPL-002` →
`E-IMPL-001`]

## Implemented state and inference semantics

<!-- trace: C-IMPL-001 C-IMPL-003 E-IMPL-001 -->

The CSM state order is IDLE, BIRTH, REINFORCE, DECAY, and DEATH, with legal
transitions encoded by the module-level mask. At sequence start, the
implementation places all CSM probability on DEATH. The CSM also applies an
anti-self-loop logit penalty and a temperature-scaled softmax.

RMP/TIP uses four-head cross-edge attention. Its latent is sampled with
`torch.randn_like` on every forward call; there is no evaluation-mode branch
that substitutes the mean. Consequently repeated inference can be stochastic
unless the random generator is controlled. [Trace: `C-IMPL-003` →
`E-IMPL-001`]

SCP uses the flattened final CSM distribution as its primary path and a weaker
global-plus-TIP auxiliary path. The returned `compliance` value is learned by a
head; it is not evidence of causal compliance. [Trace: `C-IMPL-001` →
`E-IMPL-001`]

## Loss and execution boundary

<!-- trace: C-IMPL-002 C-IMPL-003 E-IMPL-001 -->

The current loss combines prediction, TIP KL, learned-compliance, pseudo-state
supervision, diversity, commitment, temporal smoothness, state-balance,
stagnation, and lifecycle terms. Several weights and comments differ from the
older algorithm document. Training and data download live in the same module,
but import-time directory creation and random seeding have been removed.

## Known documentation conflicts

<!-- trace: C-IMPL-003 H-CAUSAL-001 E-IMPL-001 E-LEGACY-ARTIFACTS-001 -->

The older `docs/ALGORITHM.md` describes three input features, deterministic TIP
inference, different loss details, theorem/uniqueness language, and unrestricted
domain transfer. It is a historical specification, not the semantic owner of
current behavior. Method admission remains blocked until equations, tensor
contracts, transition semantics, stochastic inference, and loss behavior have
focused numerical tests.
