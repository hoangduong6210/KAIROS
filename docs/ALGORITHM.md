# RS-GNN Algorithm Specification (Detailed)

## Overview

RS-GNN (Resonance Symbolic Graph Neural Network) is the core engine of KAIROS. It compiles continuous event streams into causally valid temporal interaction graphs through a 4-layer pipeline: **RSE → CSM → RMP-TIP → SCP**.

---

## Layer 1: Resonance Signal Encoder (RSE)

### Purpose
Transform raw edge features into informativeness-weighted representations. Suppress noise, amplify signals at momentum inflection points.

### Input
- `x`: Tensor `[B, T, E, 3]` — batch of sequences
  - Feature 0: `momentum_flow = z_off[v] - z_on[u]` (flight-to-safety)
  - Feature 1: `acceleration = Δ(momentum_flow)` (rate of change)
  - Feature 2: `magnitude = |z_on[u]| + |z_off[v]|` (activity level)

### Formula
```
H_RSE(e_k) = H_type(r_k) · (1 - Sim(e_k, ē_t)) · σ(Δt/τ) · Φ_acc(acc_k)
```

### Components
1. **Type Encoder** `H_type`: `Linear(3→32) → LayerNorm → GELU`
2. **Acceleration Gate** `Φ_acc`: `Linear(1→16) → Tanh → Linear(16→1) → Sigmoid`
   - KEY INNOVATION: detects momentum inflection before magnitude grows
   - Full form: `Φ_acc(a) = 1 + α · tanh(w_a^T · [a, |a|, a²] + b_a)`
3. **Novelty Gate** `1 - Sim`: `1 - sigmoid(Linear(3→1)(x))` — suppresses redundant signals
4. **Output Projection**: `Linear(32→32)` weighted by informativeness score

### Output
- `h_out`: `[B, T, E, 32]` — informativeness-weighted edge representations
- `score`: `[B, T, E]` — per-edge informativeness scores (used in RSE ranking)

---

## Layer 2: Causal State Machine (CSM)

### Purpose
Track the symbolic lifecycle of each causal edge through 5 states with differentiable constraints.

### States
| ID | State | Meaning | Financial | Epidemiology |
|---|---|---|---|---|
| 0 | IDLE | Dormant | No inter-asset relationship | No transmission |
| 1 | BIRTH | ★ Forming | New causal link appearing | New transmission route |
| 2 | REINFORCE | Active | Contagion confirmed | Sustained spread |
| 3 | DECAY | Weakening | Mean reversion starting | Containment working |
| 4 | DEATH | Dissolved | Independence restored | Route closed |

### Transition Mask M (5×5 binary)
```
         IDLE  BIRTH  REINF  DECAY  DEATH
IDLE    [  1     1      0      0      0  ]
BIRTH   [  0     1      1      1      0  ]
REINF   [  0     0      1      1      0  ]
DECAY   [  0     0      1      1      1  ]
DEATH   [  1     0      0      0      1  ]
```

**Blocked transitions encode domain physics:**
- IDLE → REINFORCE: Cannot have full contagion without BIRTH first
- IDLE → DECAY: Cannot weaken what hasn't formed
- BIRTH → DEATH: Cannot die before activating
- REINFORCE → IDLE: Cannot instantly reset from active contagion

### Update Equations (per edge, per timestep)
```
h_t = GRU(e_uv(t), h_{t-1})           # GRU hidden state update
z_t = ReLU(W_μ · h_t + b_μ)           # Bottleneck compression
r_t = W_s · z_t + b_s                  # Raw state logits (5-dim)
p_t = Softmax(r_t + log(p_{t-1} · M + ε))  # Masked state probabilities
```

### Differentiability (Proposition 1)
The `log(p_{t-1} · M + ε)` mechanism:
- For valid transitions: `log(p + ε) ≈ log(p)` — normal gradient flow
- For blocked transitions: `log(0 + ε) = log(ε) → -∞` — drives probability to 0
- ε > 0 ensures no log(0), fully differentiable
- Gradients flow through softmax, log, and matrix multiplication

### CSM Supervision Loss
```
L_CSM = -(1/E) Σ_e Σ_s w̃_s · ỹ_e^(s) · log(p_e^(s))
```
Class weights: `w̃_BIRTH = 3, w̃_DEATH = 5` (rare but informative states upweighted)

---

## Layer 3: Resonance Message Passing (RMP) + Temporal Information Parsimony (TIP)

### RMP — Message Computation
Each edge produces a momentum-conditioned message:
```
msg_in = [z_uv(24), p_uv(5), mom_uv(1), acc_uv(1)]  # 31-dim
m_uv = ReLU(W_m · msg_in + b_m)                        # → 48-dim
z_msg = Linear(48→24)(m_uv)                             # → 24-dim message
```

### Global Aggregation
```
g(t) = (1/E) Σ_{(u,v)} m_uv(t)        # Mean-pool messages
h_global(t) = GRU(g(t), h_global(t-))  # Update global state
```

### TIP — Variational Bottleneck
Compress global representation to minimal sufficient statistic:
```
z_pool = mean(z_msg, dim=edges)  # [B, 24]
μ = W_μ^tip · z_pool + b_μ^tip  # Mean
log σ² = W_σ^tip · z_pool + b_σ^tip  # Log-variance
z_tip = μ + ε · σ,  ε ~ N(0, I)  # Reparameterization trick (training)
z_tip = μ                         # Deterministic (inference)
```

### TIP Loss (implements compression term of Eq. 2)
```
L_TIP = KL(q(z|E_≤t) ‖ N(0,I)) = (1/2) Σ_j (μ_j² + σ_j² - log σ_j² - 1)
```

### Global Projection
```
z_flat = z_msg.reshape(B, E*24)   # Flatten all edge messages
z_global = Linear(E*24 → 48)(z_flat)  # Project to global feature
```

---

## Layer 4: Symbolic Causal Policy (SCP)

### Purpose
Produce regime predictions while enforcing causal admissibility.

### Prediction
```
z_in = [z_global(48); z_tip(24)]  # Concatenate: 72-dim
logits = MLP(z_in)                 # Linear(72→64) → LN → GELU → Dropout → Linear(64→32) → GELU → Linear(32→2)
```

### Causal Masking
```
p̄ = mean(p_uv, dim=edges)  # Mean CSM state distribution [B, 5]
mask = ones(B, 2)
mask[:, BULLISH] = 0.3  if p̄[:, REINFORCE] > 0.30  # High contagion → suppress bullish
mask[:, BEARISH] = 0.3  if p̄[:, IDLE] > 0.50       # High calm → suppress bearish

ŷ = Softmax(logits + log(mask + ε))  # Masked softmax
```

### Compliance Score
```
c_t = sigmoid(MLP(z_in))  # Learned compliance: [0, 1]
```

---

## Structural Resonance (CFI Computation)

### Not a learned output — computed directly from CSM states

```python
# Per edge:
Ψ_e(t) = 1.5 * P(BIRTH) + 3.0 * P(REINFORCE)²   # Panic signal
Γ_e(t) = (|mom_e| + 2*|acc_e|) / 3                # Activity
n_active = count(edges where P(BIRTH)+P(REINFORCE)+P(DEATH) > 0.3)
Λ(t) = exp(n_active / E)                           # Contagion multiplier

# Aggregate:
SR(t) = tanh(mean_e[Ψ_e · Γ_e · Λ] · 0.5) · 100  # 0-100
CFI(t) = 100 - SR(t)                                # Inverted
```

### Design rationale:
- **BIRTH enters linearly** (weight 1.5): dominates at onset → early detection
- **REINFORCE enters quadratically** (weight 3.0): dominates at peak → crisis tracking
- **Acceleration weighted 2×**: prioritizes inflection over magnitude
- **Exponential contagion**: superlinear amplification when many edges activate

---

## Early Warning Score (EWS)

```
EWS_bear = 2·P̄(BIRTH) + 5·[ΔP̄(BIRTH)]⁺ + 1.5·|ā| + [f̄]⁺
EWS_bull = 2·P̄(DEATH) + 5·[-ΔP̄(BIRTH)]⁺ + 1.5·|ā| + [-f̄]⁺
```
Where P̄ = edge-averaged, Δ = temporal difference, [·]⁺ = max(·, 0)

---

## Unified Training Loss

```
L = L_pred + β·L_TIP + γ·L_causal + λ·L_CSM
```

| Term | Formula | Weight | Purpose |
|---|---|---|---|
| L_pred | Class-balanced BCE(ŷ, y) | 1.0 | Regime classification |
| L_TIP | KL(q(z) ‖ N(0,I)) | β=0.02 | Information compression |
| L_causal | mean(1 - c_t) | γ=0.05 | Causal compliance |
| L_CSM | Weighted CE on edge states | λ=0.2 | CSM state supervision |

### Pseudo-labels
- **Regime:** y=1 (bearish) if mean risk-on z-score drops > 0.7 in next 15 days
- **CSM states:** Rule-based from momentum flow and acceleration thresholds

---

## Causal Trace (Theorem 3)

Every Structural Resonance SR(t) decomposes uniquely:
```
SR(t) = Σ_e w_e(t) · [Ψ_e(t) · Γ_e(t)] · C

where w_e = Ψ_e·Γ_e / Σ_{e'} Ψ_{e'}·Γ_{e'}
      Σ w_e = 1, w_e ≥ 0
```

Each w_e is the **causal attribution** of edge e to the regime signal.
- High w_e → this edge is driving the prediction
- Can inspect: which assets, what state, when it transitioned
- If trace contradicts observed data → manipulation/anomaly detected

---

## Model Size

| Component | Parameters |
|---|---|
| RSE (FCE++) | ~2,200 |
| CSM (GRU + logits) | ~12,500 |
| RMP (msg_proj) | ~4,800 |
| TIP (gib_enc) | ~1,200 |
| Global projection | ~40,800 |
| SCP (classifier + compliance) | ~9,000 |
| **Total** | **~70,518** |

Lightweight: 70K params vs millions for transformer-based temporal graph models.

---

## Domain-Agnostic Mapping

| RS-GNN Concept | Finance | Epidemiology | Social Network |
|---|---|---|---|
| Nodes | Asset clusters | Geographic regions | User communities |
| Edges | Risk-ON → Risk-OFF | High-risk → Low-risk | Influencer → Follower |
| BIRTH | New capital flow | New transmission route | New influence pathway |
| REINFORCE | Sustained contagion | Sustained spread | Viral cascade |
| DECAY | Mean reversion | Containment | Interest waning |
| DEATH | Independence | Route closed | Influence lost |
| CFI/COI | Causal Fear Index | Causal Outbreak Index | Causal Cascade Index |

**Zero architecture changes required** — only edge construction and CSM interpretation change.
