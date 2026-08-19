#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Duong Viet Hoang
# SPDX-FileCopyrightText: 2026 Lun-Min Shih
# SPDX-FileCopyrightText: 2026 Yi-Hao Lai
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Modified from the previously distributed KAIROS source.
# Modification date: 2026-08-19. See NOTICE for provenance and license scope.
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  KAIROS V4 — Kausal AI for Regime Onset Sensing                            ║
║  SR-GNN (Symbolic Resonance Graph Neural Network) — Correlation Features   ║
║                                                                              ║
║  Key changes from V3:                                                        ║
║    1. 8D edge features (+rolling_corr, corr_change, spread, vol_ratio)      ║
║    2. Correlation-based CSM pseudo-labels (BIRTH = corr change spike)       ║
║    3. RMP messages now include corr + corr_change channels                  ║
║    4. SR formula uses correlation for impact weighting                       ║
║    5. All V3 architecture preserved (cap-weighted, cross-edge attn, etc.)   ║
║    6. Per-edge learnable bias & scale in CSMCell                             ║
║                                                                              ║
║  Pipeline:                                                                   ║
║    Raw Events → [L1] RSE → [L2] CSM → [L3] RMP+TIP → [L4] SCP             ║
║    → CFI (0-100) → Overlay vs F&G → Granger Tests → Figures                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import datetime
import requests
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as Fin
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import balanced_accuracy_score
from scipy import stats

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Constants & Configuration ───────────────────────────────────────────────

SEED = 42
DEVICE = torch.device("cpu")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
FIG_DIR = os.path.join(PROJECT_DIR, "runs", "model", "figures")

RISK_ON = {
    "Crypto_SuperRisk": ["BTC-USD", "ETH-USD"],
    "US_Equities":      ["SPY", "QQQ", "IWM"],
    "Global_Equities":  ["EEM", "VGK", "EWJ"],
    "Growth_Sectors":   ["XLK", "XLY", "XLF"],
    "Industrial_Comm":  ["USO", "DBB"],
    "High_Yield":       ["HYG", "JNK"],
    "Forex_Risk_On":    ["AUDUSD=X", "EURUSD=X"],
}
RISK_OFF = {
    "US_Treasuries":     ["TLT", "IEF", "SHY"],
    "Precious_Metals":   ["GLD", "SLV"],
    "Defensive_Sectors": ["XLU", "XLV", "XLP"],
    "Safe_Haven_FX":     ["JPY=X", "DX-Y.NYB"],
    "Volatility":        ["^VIX"],
}

ON_NAMES = list(RISK_ON.keys())    # 7
OFF_NAMES = list(RISK_OFF.keys())  # 5
N_EDGES = len(ON_NAMES) * len(OFF_NAMES)  # 35

CFG = {
    "seq_len":       20,
    "hidden":        48,
    "gib_dim":       24,
    "n_edges":       35,
    "n_feat":        8,       # V4: flow, accel, mag, cap_ratio, rolling_corr, corr_change, spread, vol_ratio
    "lr":            1e-3,
    "wd":            5e-4,
    "epochs":        120,
    "patience":      30,
    "batch":         256,
    "beta_tip":      0.02,
    "gamma_causal":  0.05,
    "seed":          42,
    "start":         "2014-01-01",
    "end":           "2025-04-30",
    "train_end":     "2020-12-31",
    "val_end":       "2022-12-31",
}


def set_seed(seed: int) -> None:
    """Seed KAIROS-owned random generators without mutating importers at import time."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

# CSM states
S_IDLE, S_BIRTH, S_REINFORCE, S_DECAY, S_DEATH = 0, 1, 2, 3, 4
STATE_NAMES = ["IDLE", "BIRTH", "REINFORCE", "DECAY", "DEATH"]
N_STATES = 5

# IDLE = relationship doesn't exist NOW (edge inactive, zero contribution)
# DEATH → IDLE: relationship ended, edge goes silent, waits for new BIRTH
# IDLE edges are TRANSPARENT: they don't contribute to CFI or regime prediction
# This forces model to transition to non-IDLE states when it needs to make predictions

TRANSITION_MASK = torch.tensor([
    [1, 1, 0, 0, 0],   # IDLE       -> {IDLE, BIRTH}
    [0, 1, 1, 1, 0],   # BIRTH      -> {BIRTH, REINFORCE, DECAY}
    [0, 0, 1, 1, 0],   # REINFORCE  -> {REINFORCE, DECAY}
    [0, 0, 1, 1, 1],   # DECAY      -> {DECAY, REINFORCE, DEATH}
    [1, 0, 0, 0, 1],   # DEATH      -> {IDLE, DEATH}
], dtype=torch.float32)


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 1 — DATA PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def download_market_data():
    """Download all tickers via yfinance, return DataFrame of adj close."""
    import yfinance as yf
    all_tickers = []
    for cluster in list(RISK_ON.values()) + list(RISK_OFF.values()):
        all_tickers.extend(cluster)
    all_tickers = list(dict.fromkeys(all_tickers))

    print(f"[DATA] Downloading {len(all_tickers)} tickers from {CFG['start']} to {CFG['end']} ...")
    raw = yf.download(all_tickers, start=CFG["start"], end=CFG["end"],
                       auto_adjust=True, progress=False, threads=True)

    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw

    prices = prices.ffill().bfill()
    print(f"[DATA] Downloaded {prices.shape[0]} trading days, {prices.shape[1]} tickers")
    return prices


def build_clusters_cap_weighted(prices):
    """Cap-weighted cluster z-scores using median price as cap proxy."""
    print("[DATA] Building cap-weighted cluster z-scores ...")
    log_ret = np.log(prices / prices.shift(1)).fillna(0)
    roll_mean = log_ret.rolling(20, min_periods=5).mean()
    roll_std = log_ret.rolling(20, min_periods=5).std().replace(0, 1e-8)
    z_all = (log_ret - roll_mean) / roll_std
    z_all = z_all.fillna(0).clip(-5, 5)

    # Median price across entire date range as rough cap proxy
    median_prices = prices.median()

    def cluster_weighted(cluster_dict):
        out = {}
        for name, tickers in cluster_dict.items():
            avail = [t for t in tickers if t in z_all.columns]
            if avail:
                weights = median_prices[avail].values.astype(float)
                weights = np.nan_to_num(weights, nan=1.0)
                weights = np.maximum(weights, 1e-8)
                weights = weights / weights.sum()
                out[name] = (z_all[avail].values * weights[np.newaxis, :]).sum(axis=1)
                out[name] = pd.Series(out[name], index=z_all.index)
                print(f"    {name}: tickers={avail}, weights={np.round(weights, 3).tolist()}")
            else:
                out[name] = pd.Series(0.0, index=z_all.index)
        return pd.DataFrame(out)

    z_on = cluster_weighted(RISK_ON)
    z_off = cluster_weighted(RISK_OFF)
    print(f"[DATA] Cluster z-scores: {z_on.shape[0]} days, ON={z_on.shape[1]}, OFF={z_off.shape[1]}")
    return z_on, z_off, median_prices


def build_edge_features(z_on, z_off, median_prices):
    """Build 35 macro edges x 8 features: flow, accel, mag, cap_ratio, rolling_corr, corr_change, spread, vol_ratio."""
    print("[DATA] Building edge features (8D: flow, accel, mag, cap_ratio, rolling_corr, corr_change, spread, vol_ratio) ...")
    dates = z_on.index
    n_days = len(dates)
    edge_data = np.zeros((n_days, N_EDGES, 8), dtype=np.float32)
    edge_names = []

    idx = 0
    for on_name in ON_NAMES:
        for off_name in OFF_NAMES:
            # Original 4 features
            flow = z_off[off_name].values - z_on[on_name].values
            acc = np.concatenate([[0], np.diff(flow)])
            mag = np.abs(z_on[on_name].values) + np.abs(z_off[off_name].values)

            # Cap ratio: log ratio of source vs target cluster median price
            on_tickers = [t for t in RISK_ON[on_name] if t in median_prices.index]
            off_tickers = [t for t in RISK_OFF[off_name] if t in median_prices.index]
            cap_u = median_prices[on_tickers].median() if on_tickers else 1.0
            cap_v = median_prices[off_tickers].median() if off_tickers else 1.0
            cap_ratio_val = float(np.log(cap_u / cap_v + 1e-8))
            cap_ratio = np.full(n_days, cap_ratio_val, dtype=np.float32)

            # NEW 4 features (V4: correlation-based)
            on_series = z_on[on_name]
            off_series = z_off[off_name]
            rolling_corr = on_series.rolling(20, min_periods=5).corr(off_series).fillna(0).values.astype(np.float32)
            corr_change = np.concatenate([[0], np.diff(rolling_corr)])
            corr_change = np.nan_to_num(corr_change, nan=0.0).astype(np.float32)
            spread = (z_on[on_name].values - z_off[off_name].values).astype(np.float32)  # opposite of flow
            on_vol = on_series.rolling(20, min_periods=5).std().fillna(1e-8).values.astype(np.float32)
            off_vol = off_series.rolling(20, min_periods=5).std().fillna(1e-8).values.astype(np.float32)
            vol_ratio = (on_vol / (off_vol + 1e-8)).astype(np.float32)

            edge_data[:, idx, 0] = flow.astype(np.float32)
            edge_data[:, idx, 1] = acc.astype(np.float32)
            edge_data[:, idx, 2] = mag.astype(np.float32)
            edge_data[:, idx, 3] = cap_ratio
            edge_data[:, idx, 4] = rolling_corr
            edge_data[:, idx, 5] = corr_change
            edge_data[:, idx, 6] = spread
            edge_data[:, idx, 7] = vol_ratio

            edge_names.append(f"{on_name}->{off_name}")
            idx += 1

    # Replace any remaining NaN with 0
    edge_data = np.nan_to_num(edge_data, nan=0.0)
    print(f"[DATA] Edge features: {edge_data.shape}  (T, E, 8)")
    return edge_data, dates, edge_names


def make_pseudo_labels(z_on, lookahead=15, threshold=0.7):
    """y=1 (BEARISH) if mean risk-on z drops > threshold in next lookahead days."""
    mean_on = z_on.mean(axis=1).values
    mean_on_smooth = pd.Series(mean_on).rolling(5, min_periods=1).mean().values
    n = len(mean_on_smooth)
    drops = np.zeros(n)
    for i in range(n - lookahead):
        future_min = np.min(mean_on_smooth[i + 1: i + 1 + lookahead])
        drops[i] = mean_on_smooth[i] - future_min

    adaptive_thr = max(threshold,
                       np.percentile(drops[drops > 0], 75) if np.any(drops > 0) else threshold)
    labels = (drops > adaptive_thr).astype(np.int64)

    if labels.mean() > 0.35:
        adaptive_thr = np.percentile(drops, 65)
        labels = (drops > adaptive_thr).astype(np.int64)

    print(f"[DATA] Pseudo-labels: BULLISH={np.sum(labels==0)}, BEARISH={np.sum(labels==1)} "
          f"({100*np.mean(labels):.1f}% bearish, thr={adaptive_thr:.3f})")
    return labels


def make_edge_state_labels(edge_data):
    """V4: Correlation-based pseudo-labels.
    corr_change > 0 (large) -> BIRTH (relationship forming)
    corr stable at high level -> REINFORCE
    corr_change < 0 -> DECAY (relationship weakening)
    corr near 0 -> DEATH/IDLE
    """
    T, E, _ = edge_data.shape
    states = np.zeros((T, E), dtype=np.int64)  # IDLE=0

    for e in range(E):
        corr = edge_data[:, e, 4]          # rolling_corr (feature index 4)
        corr_chg = edge_data[:, e, 5]      # corr_change (feature index 5)
        abs_flow = np.abs(edge_data[:, e, 0])

        # Per-edge adaptive thresholds
        valid_cc = corr_chg[~np.isnan(corr_chg)]
        valid_cr = corr[~np.isnan(corr)]
        if len(valid_cc) == 0 or len(valid_cr) == 0:
            continue
        corr_chg_p90 = np.percentile(np.abs(valid_cc), 90)
        corr_chg_p75 = np.percentile(np.abs(valid_cc), 75)
        corr_high = np.percentile(np.abs(valid_cr), 70)

        current = 0  # IDLE
        for t in range(T):
            cc = corr_chg[t] if not np.isnan(corr_chg[t]) else 0
            cr = corr[t] if not np.isnan(corr[t]) else 0

            if abs(cc) > corr_chg_p90 and current in [0, 4]:
                current = 1  # BIRTH — correlation changing rapidly
            elif abs(cr) > corr_high and current in [1, 2]:
                current = 2  # REINFORCE — correlation stable at high level
            elif abs(cc) > corr_chg_p75 and cc < 0 and current in [1, 2, 3]:
                current = 3  # DECAY — correlation weakening
            elif abs(cr) < corr_high * 0.3 and current in [3]:
                current = 4  # DEATH — correlation returned to low
            elif abs(cr) < corr_high * 0.2 and current in [4]:
                current = 0  # IDLE — no relationship

            states[t, e] = current

    # Print distribution
    for s in range(5):
        pct = 100.0 * (states == s).sum() / states.size
        print(f"  CSM label {['IDLE','BIRTH','REINFORCE','DECAY','DEATH'][s]}: {pct:.1f}%")

    return states


def create_sequences(edge_data, labels, edge_states, seq_len=20):
    """Sliding window sequences WITH edge state labels for CSM supervision."""
    n = len(labels)
    X_list, Y_list, S_list = [], [], []
    for i in range(n - seq_len):
        X_list.append(edge_data[i: i + seq_len])
        Y_list.append(labels[i + seq_len - 1])
        S_list.append(edge_states[i: i + seq_len])
    X = np.array(X_list, dtype=np.float32)
    Y = np.array(Y_list, dtype=np.int64)
    S = np.array(S_list, dtype=np.int64)
    print(f"[DATA] Sequences: X={X.shape}, Y={Y.shape}, S={S.shape}")
    return X, Y, S


def fetch_fear_greed():
    """Fetch CNN Fear & Greed proxy from alternative.me."""
    print("[DATA] Fetching Fear & Greed index ...")
    try:
        resp = requests.get("https://api.alternative.me/fng/?limit=4000&format=json", timeout=30)
        data = resp.json()["data"]
        records = []
        for d in data:
            ts = int(d["timestamp"])
            dt = datetime.datetime.utcfromtimestamp(ts).date()
            records.append({"date": pd.Timestamp(dt), "fng": int(d["value"])})
        df = pd.DataFrame(records).sort_values("date").drop_duplicates("date").set_index("date")
        print(f"[DATA] Fear & Greed: {len(df)} days, range {df.index.min()} to {df.index.max()}")
        return df
    except Exception as e:
        print(f"[WARN] Could not fetch F&G: {e}. Using VIX-based proxy.")
        idx = pd.date_range("2018-02-01", "2025-04-30", freq="B")
        return pd.DataFrame({"fng": 50 + 20 * np.sin(np.arange(len(idx)) * 0.02)}, index=idx)


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — SR-GNN V3 MODEL
# ════════════════════════════════════════════════════════════════════════════

# ── Layer 1: RSE (Resonance Signal Encoder) ─────────────────────────────────

class RSE(nn.Module):
    """Resonance Signal Encoder — Layer 1. V4: handles 8 input features."""

    def __init__(self, n_feat=8, hidden=32):
        super().__init__()
        self.h_type = nn.Sequential(
            nn.Linear(n_feat, hidden), nn.LayerNorm(hidden), nn.GELU()
        )
        self.phi_acc = nn.Sequential(
            nn.Linear(1, 16), nn.Tanh(), nn.Linear(16, 1), nn.Sigmoid()
        )
        self.sim_proj = nn.Linear(n_feat, 1)

    def forward(self, x):
        """x: [B, T, E, 8] -> h: [B, T, E, hidden], scores: [B, T, E]"""
        h = self.h_type(x)                                         # [B,T,E,hidden]
        sim = 1.0 - torch.sigmoid(self.sim_proj(x)).squeeze(-1)    # [B,T,E]
        acc = x[..., 1:2]                                          # [B,T,E,1]
        phi = self.phi_acc(acc).squeeze(-1)                        # [B,T,E]
        scores = sim * phi                                         # [B,T,E]
        h = h * scores.unsqueeze(-1)                               # modulate
        return h, scores


# ── Layer 2: CSMCell (Causal State Machine — Self-Supervised) ────────────────

class CSMCell(nn.Module):
    """
    Causal State Machine cell — Layer 2.
    Self-supervised: per-edge learnable bias & scale, NO hard labels needed.
    """

    def __init__(self, in_dim=32, hidden_dim=48, gib_dim=24, n_states=5, n_edges=35):
        super().__init__()
        self.n_states = n_states
        self.n_edges = n_edges
        self.hidden_dim = hidden_dim
        self.gib_dim = gib_dim

        self.gru = nn.GRUCell(in_dim, hidden_dim)
        self.drop = nn.Dropout(0.15)
        self.gib_mu = nn.Linear(hidden_dim, gib_dim)
        self.logits_head = nn.Linear(gib_dim, n_states)
        self.register_buffer("mask", TRANSITION_MASK)

        # Per-edge learnable parameters
        self.edge_bias = nn.Parameter(torch.zeros(n_edges, n_states))
        self.edge_scale = nn.Parameter(torch.ones(n_edges, 1))

    def forward(self, x_t, h_prev, p_prev, edge_indices, temperature=1.0):
        """
        x_t:          [B*E, in_dim]
        h_prev:       [B*E, hidden_dim]
        p_prev:       [B*E, n_states]
        edge_indices: [B*E] — which edge (0..E-1) each sample belongs to
        temperature:  float — high=soft (explore), low=sharp (exploit)
        Returns: h_new, p_new, z_t
        """
        # Per-edge scaling
        scales = self.edge_scale[edge_indices]        # [B*E, 1]
        x_scaled = x_t * scales

        h_new = self.drop(self.gru(x_scaled, h_prev))
        z_t = Fin.relu(self.gib_mu(h_new))            # [B*E, gib_dim]
        raw = self.logits_head(z_t)                    # [B*E, n_states]

        # Per-edge bias
        bias = self.edge_bias[edge_indices]            # [B*E, n_states]
        raw = raw + bias

        # Symbolic transition masking
        valid = torch.matmul(p_prev, self.mask) + 1e-8
        sym = raw + torch.log(valid)

        # Anti-self-loop bias: penalize staying in same state
        # Detect current dominant state and suppress it slightly
        dominant = p_prev.argmax(dim=-1)  # [B*E]
        self_loop_penalty = torch.zeros_like(sym)
        self_loop_penalty.scatter_(1, dominant.unsqueeze(1), -0.5)  # -0.5 logit for self-loop
        sym = sym + self_loop_penalty

        # Temperature-scaled softmax
        p_new = Fin.softmax(sym / temperature, dim=-1)

        return h_new, p_new, z_t


# ── Layer 3: RMP_TIP (Resonance Message Passing + TIP + Cross-Edge Attn) ────

class RMP_TIP(nn.Module):
    """
    Resonance Message Passing + Temporal Information Parsimony — Layer 3.
    V3 additions: cross-edge multi-head attention after temporal processing.
    """

    def __init__(self, n_edges=35, rse_dim=32, n_states=5, hidden=48, gib_dim=24):
        super().__init__()
        self.n_edges = n_edges
        self.hidden = hidden
        self.gib_dim = gib_dim
        self._temperature = 5.0  # Start high (soft) — will be annealed during training

        # CSM cell (self-supervised)
        self.csm = CSMCell(in_dim=rse_dim, hidden_dim=hidden, gib_dim=gib_dim,
                           n_states=n_states, n_edges=n_edges)

        # Message network: concat(z_edge[gib_dim], p_csm[5], mom[1], acc[1], corr[1], corr_chg[1]) = gib_dim+5+4
        msg_in_dim = gib_dim + n_states + 2 + 2
        self.msg_proj = nn.Sequential(
            nn.Linear(msg_in_dim, hidden), nn.ReLU(),
            nn.Dropout(0.15), nn.Linear(hidden, gib_dim)
        )
        self.edge_proj = nn.Linear(hidden, gib_dim)
        self.global_gru = nn.GRUCell(gib_dim, hidden)
        self.flat_proj = nn.Linear(n_edges * gib_dim, hidden)

        # Cross-edge attention (V3 new)
        self.edge_attn = nn.MultiheadAttention(gib_dim, num_heads=4, batch_first=True)

        # TIP bottleneck
        self.mu_proj = nn.Linear(gib_dim, gib_dim)
        self.logvar_proj = nn.Linear(gib_dim, gib_dim)

    def forward(self, h_rse, x_raw):
        """
        h_rse:  [B, T, E, rse_dim]
        x_raw:  [B, T, E, 8]
        Returns: z_global [B, hidden], z_tip [B, gib_dim], kl scalar, edge_probs [B, T, E, 5]
        """
        B, T, E, _ = h_rse.shape

        # Build edge indices: [0,1,...,E-1] repeated B times -> [B*E]
        edge_idx = torch.arange(E, device=h_rse.device).unsqueeze(0).expand(B, -1).reshape(B * E)

        # Init CSM states
        h_csm = torch.zeros(B * E, self.hidden, device=h_rse.device)
        p_csm = torch.zeros(B * E, N_STATES, device=h_rse.device)
        p_csm[:, S_DEATH] = 1.0  # Start in DEATH → ready to BIRTH
        h_global = torch.zeros(B, self.hidden, device=h_rse.device)

        all_edge_probs = []
        all_z = []

        for t in range(T):
            x_t = h_rse[:, t].reshape(B * E, -1)               # [B*E, rse_dim]

            # CSM update
            h_csm, p_csm, z_t = self.csm(x_t, h_csm, p_csm, edge_idx, temperature=self._temperature)
            all_edge_probs.append(p_csm.reshape(B, E, N_STATES))

            # Edge latent
            z_edge = self.edge_proj(h_csm).reshape(B, E, self.gib_dim)
            all_z.append(z_edge)

            # Message features
            mom = x_raw[:, t, :, 0:1]                           # [B, E, 1]
            acc = x_raw[:, t, :, 1:2]                           # [B, E, 1]
            corr = x_raw[:, t, :, 4:5]                          # [B, E, 1] rolling correlation
            corr_chg = x_raw[:, t, :, 5:6]                      # [B, E, 1] correlation change
            p_edge = p_csm.reshape(B, E, N_STATES)
            msg_in = torch.cat([z_edge, p_edge, mom, acc, corr, corr_chg], dim=-1)
            msg = self.msg_proj(msg_in)                         # [B, E, gib_dim]

            # KEY V3.4: IDLE edges are TRANSPARENT — zero contribution to messages
            # Only non-IDLE edges (BIRTH/REINFORCE/DECAY/DEATH) contribute
            # This forces model to use non-IDLE states when it needs to make predictions
            idle_prob = p_edge[:, :, S_IDLE]                    # [B, E]
            active_weight = (1.0 - idle_prob).unsqueeze(-1)     # [B, E, 1]
            msg_weighted = msg * active_weight                  # IDLE edges → near-zero msg

            # Weighted mean (only active edges contribute)
            active_sum = active_weight.sum(dim=1).clamp(min=1e-8)  # [B, 1]
            msg_mean = msg_weighted.sum(dim=1) / active_sum     # [B, gib_dim]
            h_global = self.global_gru(msg_mean, h_global)

        edge_probs = torch.stack(all_edge_probs, dim=1)         # [B, T, E, 5]
        z_stack = torch.stack(all_z, dim=1)                     # [B, T, E, gib_dim]

        # Cross-edge attention on last timestep (V3 new)
        z_last = z_stack[:, -1]                                 # [B, E, gib_dim]
        z_attended, _ = self.edge_attn(z_last, z_last, z_last)  # [B, E, gib_dim]

        # Flat projection for z_global
        flat = z_attended.reshape(B, E * self.gib_dim)
        z_global = self.flat_proj(flat)                         # [B, hidden]

        # TIP bottleneck (from attended edge representations)
        z_pool = z_attended.mean(dim=1)                         # [B, gib_dim]
        mu = self.mu_proj(z_pool)
        logvar = self.logvar_proj(z_pool)
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        z_tip = mu + eps * std
        kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())

        return z_global, z_tip, kl_loss, edge_probs


# ── Layer 4: SCP (Symbolic Causal Policy) ────────────────────────────────────

class SCP(nn.Module):
    """Symbolic Causal Policy — Layer 4.

    V3.5 REDESIGN: CSM states are the PRIMARY input for prediction.
    z_global/z_tip only provide auxiliary context.
    This forces model to learn meaningful CSM states.
    """

    def __init__(self, n_edges=35, n_states=5, aux_dim=72):
        super().__init__()
        # PRIMARY path: CSM state distribution → prediction
        # Input: flattened CSM states [B, E*5] = [B, 175]
        csm_dim = n_edges * n_states  # 35 * 5 = 175
        self.csm_net = nn.Sequential(
            nn.Linear(csm_dim, 64), nn.LayerNorm(64), nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(64, 32), nn.GELU(),
        )

        # AUXILIARY path: z_global + z_tip provide context (but weaker)
        self.aux_net = nn.Sequential(
            nn.Linear(aux_dim, 32), nn.LayerNorm(32), nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(32, 16),
        )

        # FUSION: CSM signal (32) + aux context (16) → regime prediction
        self.fusion = nn.Sequential(
            nn.Linear(32 + 16, 16), nn.GELU(),
            nn.Linear(16, 2)
        )

        self.compliance_head = nn.Sequential(
            nn.Linear(csm_dim, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid()
        )

    def forward(self, z_global, z_tip, p_last):
        """
        z_global: [B, hidden], z_tip: [B, gib_dim], p_last: [B, E, 5]
        Returns: probs [B, 2], compliance [B]
        """
        B = p_last.shape[0]

        # PRIMARY: CSM states flatten → main prediction signal
        csm_flat = p_last.reshape(B, -1)               # [B, E*5=175]
        csm_feat = self.csm_net(csm_flat)               # [B, 32]

        # AUXILIARY: global context (weaker signal)
        aux_inp = torch.cat([z_global, z_tip], dim=-1)  # [B, 72]
        aux_feat = self.aux_net(aux_inp)                 # [B, 16]

        # FUSION
        fused = torch.cat([csm_feat, aux_feat], dim=-1)  # [B, 48]
        logits = self.fusion(fused)                       # [B, 2]

        probs = Fin.softmax(logits, dim=-1)
        compliance = self.compliance_head(csm_flat).squeeze(-1)
        return probs, compliance


# ── Full SR-GNN V3 ───────────────────────────────────────────────────────────

class SRGNN(nn.Module):
    """Full SR-GNN V4 model — 8D edge features with correlation channels."""

    def __init__(self, n_edges=35, n_feat=8, hidden=48, gib_dim=24):
        super().__init__()
        self.rse = RSE(n_feat=n_feat, hidden=32)
        self.rmp_tip = RMP_TIP(n_edges=n_edges, rse_dim=32, n_states=5,
                               hidden=hidden, gib_dim=gib_dim)
        self.scp = SCP(n_edges=n_edges, n_states=5, aux_dim=hidden + gib_dim)

    def forward(self, x):
        """x: [B, T, E, 8]"""
        h_rse, rse_scores = self.rse(x)
        z_global, z_tip, kl_loss, edge_probs = self.rmp_tip(h_rse, x)
        probs, compliance = self.scp(z_global, z_tip, edge_probs[:, -1])
        return {
            "probs": probs,
            "compliance": compliance,
            "kl_loss": kl_loss,
            "edge_probs": edge_probs,
            "rse_scores": rse_scores,
        }


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 3 — LOSS (Self-Supervised CSM, NO L_CSM with hard labels)
# ════════════════════════════════════════════════════════════════════════════

def compute_loss(out, y_true, pred_weight, esb=None):
    """
    V3.8 hybrid loss: pseudo-label supervision + self-supervised regularization.
      L_pred    — classification
      L_TIP     — KL divergence
      L_causal  — compliance penalty
      L_CSM     — edge-level CSM supervision (pseudo-labels, BIRTH=3x, DEATH=5x weight)
      L_diversity, L_commit, L_smooth, L_state_balance — self-supervised CSM regs
      L_stagnation, L_lifecycle — anti-collapse regularizers
    """
    # L_pred
    L_pred = Fin.cross_entropy(out["probs"], y_true, weight=pred_weight)

    # L_TIP
    L_TIP = out.get("kl_loss", torch.tensor(0.0, device=DEVICE))

    # L_causal
    L_causal = (1.0 - out.get("compliance", torch.ones(1, device=DEVICE))).mean()

    edge_probs = out["edge_probs"]  # [B, T, E, 5]

    # L_diversity: global state distribution should be non-uniform (entropy maximized)
    mean_state = edge_probs[:, -1].mean(dim=1)  # [B, 5] mean across edges
    L_diversity = -torch.distributions.Categorical(
        probs=mean_state + 1e-8
    ).entropy().mean()

    # L_commit: each edge should commit to 1 state (low per-edge entropy)
    per_edge_ent = torch.distributions.Categorical(
        probs=edge_probs[:, -1] + 1e-8
    ).entropy()  # [B, E]
    L_commit = per_edge_ent.mean()

    # L_smooth: temporal KL between consecutive timesteps
    if edge_probs.shape[1] > 1:
        p_curr = edge_probs[:, 1:]    # [B, T-1, E, 5]
        p_prev = edge_probs[:, :-1]   # [B, T-1, E, 5]
        L_smooth = Fin.kl_div(
            (p_curr + 1e-8).log(), p_prev + 1e-8,
            reduction="batchmean", log_target=False
        )
    else:
        L_smooth = torch.tensor(0.0, device=DEVICE)

    # L_state_balance: All 5 states should have meaningful usage
    # IDLE is allowed to dominate (up to 70%) since many edges genuinely inactive
    # But non-IDLE states must each have >= 3% when they appear
    state_usage = edge_probs[:, -1].mean(dim=(0, 1))  # [5] mean across batch+edges
    # Non-IDLE states (BIRTH/REINFORCE/DECAY/DEATH) must each have some minimum
    non_idle_usage = state_usage[1:]  # [4] — skip IDLE
    L_state_floor = Fin.relu(0.03 - non_idle_usage).sum() * 5.0  # each non-IDLE >= 3%
    # IDLE should not dominate completely (< 80%)
    L_idle_cap = Fin.relu(state_usage[0] - 0.80) * 5.0
    L_state_balance = L_state_floor + L_idle_cap

    # L_transition: PENALIZE self-loops over time — force state CHANGES
    # If edge stays in same state across entire sequence, it's not modeling lifecycle
    if edge_probs.shape[1] >= 5:
        # Compare first half vs second half of sequence
        p_first = edge_probs[:, :edge_probs.shape[1]//2].mean(dim=1)  # [B, E, 5]
        p_second = edge_probs[:, edge_probs.shape[1]//2:].mean(dim=1)  # [B, E, 5]
        # Cosine similarity between first and second half — high = stagnant
        cos_sim = Fin.cosine_similarity(p_first.reshape(-1, N_STATES),
                                         p_second.reshape(-1, N_STATES), dim=-1)
        L_stagnation = cos_sim.mean()  # 1.0 = perfectly stagnant, 0.0 = changed
    else:
        L_stagnation = torch.tensor(0.0, device=DEVICE)

    # L_lifecycle: encourage the FULL cycle — reward edges that visit multiple states
    # Count how many states each edge visits (entropy of time-averaged distribution)
    time_avg = edge_probs.mean(dim=1)  # [B, E, 5] average over time
    lifecycle_entropy = torch.distributions.Categorical(probs=time_avg + 1e-8).entropy()  # [B, E]
    L_lifecycle = -lifecycle_entropy.mean()  # negative → maximize → more states visited

    # L_CSM: supervised edge-level state prediction (pseudo-labels)
    L_CSM = torch.tensor(0.0, device=DEVICE)
    if esb is not None and "edge_probs" in out:
        ep = out["edge_probs"]          # [B, T, E, 5]
        # Class weights: BIRTH=10 (very rare, very important), DEATH=5, others=1
        csm_weight = torch.tensor([1.0, 10.0, 1.0, 1.0, 5.0], device=DEVICE)
        ep_flat = ep.reshape(-1, N_STATES)
        es_flat = esb.reshape(-1)
        L_CSM = Fin.cross_entropy(ep_flat, es_flat, weight=csm_weight)

    # Total — balanced: classification + CSM supervision + regularizers
    L = (1.0 * L_pred
         + CFG["beta_tip"] * L_TIP
         + CFG["gamma_causal"] * L_causal
         + 0.3 * L_CSM             # balanced: teach CSM but don't kill classification
         + 0.01 * L_diversity
         + 0.01 * L_commit
         + 0.005 * L_smooth
         + 0.1 * L_state_balance
         + 0.02 * L_stagnation
         + 0.01 * L_lifecycle)

    return L


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 4 — TRAINING
# ════════════════════════════════════════════════════════════════════════════

def compute_stage1_loss(model, xb):
    """Stage 1 loss: CSM must predict next-timestep features (no classification).

    This forces CSM to learn meaningful states because:
    - BIRTH state must predict increasing correlation → learn to detect onset
    - REINFORCE must predict stable high correlation → learn to detect persistence
    - DECAY must predict decreasing correlation → learn to detect weakening
    - Different states must predict DIFFERENTLY → states differentiate
    """
    B, T, E, Feat = xb.shape
    if T < 3:
        return torch.tensor(0.0, device=DEVICE)

    out = model(xb)
    edge_probs = out["edge_probs"]  # [B, T, E, 5]

    # For each timestep, use CSM state to predict next timestep's features
    # Prediction: weighted combination of state-specific prediction heads
    # Simplified: use mean of edge_probs-weighted features as prediction
    total_pred_loss = torch.tensor(0.0, device=DEVICE)
    n_steps = 0

    for t in range(1, min(T, 15)):  # predict up to 15 steps ahead
        p_t = edge_probs[:, t-1]     # [B, E, 5] CSM state at t-1
        x_actual = xb[:, t, :, :4]   # [B, E, 4] actual features at t (first 4: flow,acc,mag,cap)

        # State-conditioned prediction: each state predicts a "direction"
        # BIRTH (1): predict increasing |flow| → target = x_actual should be larger
        # REINFORCE (2): predict stable → target = similar to previous
        # DECAY (3): predict decreasing → target = smaller
        # DEATH (4): predict near-zero
        # IDLE (0): predict noise around 0

        x_prev = xb[:, t-1, :, :4]  # [B, E, 4]
        delta = x_actual - x_prev    # [B, E, 4] actual change

        # CSM should predict the SIGN and MAGNITUDE of change
        # State-weighted expected change direction:
        # BIRTH → positive change expected (relationship strengthening)
        # REINFORCE → near-zero change (stable)
        # DECAY → negative change (weakening)
        # DEATH → near-zero (flat)
        # IDLE → near-zero (flat)
        expected_sign = (
            p_t[:, :, S_BIRTH] * 1.0 +          # BIRTH: expect positive change
            p_t[:, :, S_REINFORCE] * 0.0 +       # REINFORCE: expect no change
            p_t[:, :, S_DECAY] * (-1.0) +        # DECAY: expect negative change
            p_t[:, :, S_DEATH] * 0.0 +           # DEATH: expect no change
            p_t[:, :, S_IDLE] * 0.0              # IDLE: expect no change
        )  # [B, E]

        # Loss: predicted sign should match actual delta sign (on flow feature)
        actual_sign = delta[:, :, 0]  # flow change [B, E]
        sign_loss = Fin.mse_loss(expected_sign, actual_sign.sign())

        # Also: state entropy should be reasonable (commit but diverse)
        state_ent = torch.distributions.Categorical(probs=p_t + 1e-8).entropy().mean()

        total_pred_loss = total_pred_loss + sign_loss - 0.01 * state_ent
        n_steps += 1

    return total_pred_loss / max(n_steps, 1)


def train_model(X, Y, dates_seq, ES=None):
    """Train SR-GNN V4 with THREE-STAGE training:

    Stage 1 (40 epochs): Train CSM as feature predictor (NO classification)
        → CSM learns meaningful states freely
    Stage 2 (60 epochs): Freeze CSM, train classification head
        → SCP learns to use CSM states for regime prediction
    Stage 3 (20 epochs): Fine-tune everything with small lr
        → End-to-end refinement
    """
    train_end = pd.Timestamp(CFG["train_end"])
    val_end = pd.Timestamp(CFG["val_end"])

    train_mask = dates_seq <= train_end
    val_mask = (dates_seq > train_end) & (dates_seq <= val_end)
    test_mask = dates_seq > val_end

    Xtr, Ytr = X[train_mask], Y[train_mask]
    Xval, Yval = X[val_mask], Y[val_mask]
    Xte, Yte = X[test_mask], Y[test_mask]
    EStr = ES[train_mask] if ES is not None else None

    print(f"[TRAIN] Splits: train={len(Ytr)}, val={len(Yval)}, test={len(Yte)}")
    print(f"[TRAIN] Train bearish rate: {Ytr.mean():.3f}")

    Xtr_t = torch.from_numpy(Xtr).to(DEVICE)
    Ytr_t = torch.from_numpy(Ytr).to(DEVICE)
    Xval_t = torch.from_numpy(Xval).to(DEVICE)
    Yval_t = torch.from_numpy(Yval)
    EStr_t = torch.from_numpy(EStr).to(DEVICE) if EStr is not None else None

    train_ds = TensorDataset(Xtr_t, Ytr_t)
    train_dl = DataLoader(train_ds, batch_size=CFG["batch"], shuffle=True, drop_last=False)

    model = SRGNN(n_edges=CFG["n_edges"], n_feat=CFG["n_feat"],
                  hidden=CFG["hidden"], gib_dim=CFG["gib_dim"]).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[MODEL] Parameters: {n_params:,}")

    pos_rate = max(Ytr.mean(), 0.05)
    w_bear = max(1.0 / (2.0 * pos_rate + 1e-8), 1.0)
    pred_weight = torch.tensor([1.0, w_bear], dtype=torch.float32, device=DEVICE)

    history = {"train_loss": [], "val_bacc": []}

    # ════════════════════════════════════════════════════════════════════
    # STAGE 1: Train CSM as feature predictor (NO classification)
    # CSM learns meaningful states by predicting next-timestep features
    # ════════════════════════════════════════════════════════════════════
    S1_EPOCHS = 60
    print(f"\n[STAGE 1] CSM pre-training ({S1_EPOCHS} epochs) — learn states from feature prediction")

    # Only train RSE + RMP_TIP (which contains CSM). Freeze SCP.
    for p in model.scp.parameters():
        p.requires_grad = False

    opt1 = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=CFG["lr"], weight_decay=CFG["wd"])
    sch1 = torch.optim.lr_scheduler.CosineAnnealingLR(opt1, T_max=S1_EPOCHS)

    for epoch in range(S1_EPOCHS):
        model.train()
        epoch_loss = 0.0; nb = 0
        # Temperature: high at start for exploration
        temperature = 3.0 * (0.5 / 3.0) ** (epoch / max(S1_EPOCHS - 1, 1))
        model.rmp_tip._temperature = temperature

        for xb, _ in train_dl:
            loss = compute_stage1_loss(model, xb)
            opt1.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt1.step()
            epoch_loss += loss.item(); nb += 1

        sch1.step()
        if (epoch + 1) % 10 == 0:
            # Check state distribution
            model.eval()
            with torch.no_grad():
                out_check = model(Xval_t[:200])
                ep = out_check["edge_probs"][:, -1]
                dom = ep.argmax(dim=-1).reshape(-1).numpy()
                dist = [100.0 * (dom == s).mean() for s in range(N_STATES)]
            print(f"  S1 Ep {epoch+1:3d}/{S1_EPOCHS}  loss={epoch_loss/nb:.4f}  temp={temperature:.2f}  "
                  f"states=[I:{dist[0]:.0f} B:{dist[1]:.0f} R:{dist[2]:.0f} D:{dist[3]:.0f} X:{dist[4]:.0f}]%")

    # ════════════════════════════════════════════════════════════════════
    # STAGE 2: Freeze CSM, train classification (SCP)
    # CSM states are now meaningful → SCP learns to use them
    # ════════════════════════════════════════════════════════════════════
    S2_EPOCHS = 80
    print(f"\n[STAGE 2] Classification training ({S2_EPOCHS} epochs) — freeze CSM, train SCP")

    # Freeze RSE + CSM, unfreeze SCP
    for p in model.rse.parameters():
        p.requires_grad = False
    for p in model.rmp_tip.parameters():
        p.requires_grad = False
    for p in model.scp.parameters():
        p.requires_grad = True

    opt2 = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=CFG["lr"], weight_decay=CFG["wd"])
    sch2 = torch.optim.lr_scheduler.CosineAnnealingLR(opt2, T_max=S2_EPOCHS)

    model.rmp_tip._temperature = 0.5  # sharp states for classification
    best_val_bacc = 0.0; best_state = None; wait = 0

    for epoch in range(S2_EPOCHS):
        model.train()
        epoch_loss = 0.0; nb = 0
        for xb, yb in train_dl:
            out = model(xb)
            loss = Fin.cross_entropy(out["probs"], yb, weight=pred_weight)
            loss += CFG["beta_tip"] * out.get("kl_loss", torch.tensor(0.0, device=DEVICE))
            opt2.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt2.step()
            epoch_loss += loss.item(); nb += 1
        sch2.step()

        model.eval()
        with torch.no_grad():
            preds_val = model(Xval_t)["probs"].argmax(dim=1).cpu().numpy()
            val_bacc = balanced_accuracy_score(Yval, preds_val)
        history["train_loss"].append(epoch_loss / nb)
        history["val_bacc"].append(val_bacc)

        if val_bacc > best_val_bacc:
            best_val_bacc = val_bacc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1

        if (epoch + 1) % 10 == 0 or wait == 0:
            print(f"  S2 Ep {epoch+1:3d}/{S2_EPOCHS}  loss={epoch_loss/nb:.4f}  "
                  f"val_bacc={val_bacc:.4f}  best={best_val_bacc:.4f}")

        if wait >= 25:
            print(f"  [S2] Early stopping at epoch {epoch+1}")
            break

    model.load_state_dict(best_state)

    # ════════════════════════════════════════════════════════════════════
    # STAGE 3: Fine-tune everything with small lr
    # ════════════════════════════════════════════════════════════════════
    S3_EPOCHS = 60
    print(f"\n[STAGE 3] Fine-tuning ({S3_EPOCHS} epochs) — all params, lr/3")

    for p in model.parameters():
        p.requires_grad = True

    opt3 = torch.optim.AdamW(model.parameters(), lr=CFG["lr"] * 0.33, weight_decay=CFG["wd"])
    model.rmp_tip._temperature = 0.3  # very sharp
    wait = 0

    for epoch in range(S3_EPOCHS):
        model.train()
        epoch_loss = 0.0; nb = 0
        for xb, yb in train_dl:
            out = model(xb)
            loss = Fin.cross_entropy(out["probs"], yb, weight=pred_weight)
            loss += CFG["beta_tip"] * out.get("kl_loss", torch.tensor(0.0, device=DEVICE))
            loss += 0.01 * compute_stage1_loss(model, xb)  # gentle CSM maintenance
            opt3.zero_grad(); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt3.step()
            epoch_loss += loss.item(); nb += 1

        model.eval()
        with torch.no_grad():
            preds_val = model(Xval_t)["probs"].argmax(dim=1).cpu().numpy()
            val_bacc = balanced_accuracy_score(Yval, preds_val)
        history["train_loss"].append(epoch_loss / nb)
        history["val_bacc"].append(val_bacc)

        if val_bacc > best_val_bacc:
            best_val_bacc = val_bacc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1

        if (epoch + 1) % 5 == 0:
            print(f"  S3 Ep {epoch+1:3d}/{S3_EPOCHS}  loss={epoch_loss/nb:.4f}  val_bacc={val_bacc:.4f}")

        if wait >= 15:
            print(f"  [S3] Early stopping at epoch {epoch+1}")
            break

    model.load_state_dict(best_state)
    model.eval()
    model.rmp_tip._temperature = 0.3

    # Test
    with torch.no_grad():
        Xte_t = torch.from_numpy(Xte).to(DEVICE)
        preds_te = model(Xte_t)["probs"].argmax(dim=1).cpu().numpy()
        test_bacc = balanced_accuracy_score(Yte, preds_te)

    print(f"\n[RESULT] Best val balanced acc: {best_val_bacc:.4f}")
    print(f"[RESULT] Test balanced acc:     {test_bacc:.4f}")

    return model, history, best_val_bacc, test_bacc, {
        "Xtr": Xtr, "Xval": Xval, "Xte": Xte,
        "Ytr": Ytr, "Yval": Yval, "Yte": Yte,
    }


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 5 — CFI COMPUTATION
# ════════════════════════════════════════════════════════════════════════════

def compute_cfi(model, X_all):
    """Compute CFI from model outputs with 5-step averaging, then EMA-7."""
    model.eval()
    n = len(X_all)
    sr_raw = np.zeros(n)
    all_edge_probs = []

    bs = 512
    for i in range(0, n, bs):
        xb = torch.from_numpy(X_all[i:i+bs]).to(DEVICE)
        with torch.no_grad():
            out = model(xb)
        ep = out["edge_probs"].cpu().numpy()       # [B, T, E, 5]
        xr = X_all[i:i+bs]                         # [B, T, E, 8]
        all_edge_probs.append(ep)

        # CSM states at different timesteps
        p_last = ep[:, -1]                           # [B, E, 5] current state
        p_prev = ep[:, -2] if ep.shape[1] > 1 else ep[:, -1]  # previous state
        p_avg = ep[:, -5:].mean(axis=1)              # [B, E, 5] smoothed
        x_last = xr[:, -5:].mean(axis=1)            # [B, E, 8]

        for j in range(len(xb)):
            # ══ COMPONENT 1: Net causal pressure (which lifecycle phase dominates) ══
            fear_pressure = (p_avg[j, :, S_BIRTH] * 2.0 +
                           p_avg[j, :, S_REINFORCE] * 3.0)
            recovery_pressure = (p_avg[j, :, S_DECAY] * 1.5 +
                               p_avg[j, :, S_DEATH] * 1.0)
            net_pressure = fear_pressure - recovery_pressure  # [E] positive = fear

            # ══ COMPONENT 2: Transition rate (how many edges CHANGED state) ══
            # This is the EARLIEST signal — mass state changes = regime transition
            dom_curr = p_last[j].argmax(axis=-1)    # [E] dominant state now
            dom_prev = p_prev[j].argmax(axis=-1)    # [E] dominant state before
            n_changed = (dom_curr != dom_prev).sum()  # how many edges switched
            transition_rate = n_changed / N_EDGES     # 0-1

            # Direction of transitions: toward fear or toward recovery?
            # IDLE→BIRTH or DECAY→REINFORCE = toward fear
            # REINFORCE→DECAY or BIRTH→DECAY = toward recovery
            fear_transitions = 0
            recovery_transitions = 0
            for e in range(N_EDGES):
                if dom_curr[e] != dom_prev[e]:
                    s_from, s_to = dom_prev[e], dom_curr[e]
                    if s_to in [S_BIRTH, S_REINFORCE]:
                        fear_transitions += 1
                    elif s_to in [S_DECAY, S_DEATH, S_IDLE]:
                        recovery_transitions += 1
            net_transition_direction = (fear_transitions - recovery_transitions) / max(n_changed, 1)

            # ══ COMPONENT 3: Feature impact (momentum × acceleration × correlation) ══
            mom = x_last[j, :, 0]
            acc = x_last[j, :, 1]
            corr = x_last[j, :, 4] if x_last.shape[-1] > 4 else np.zeros_like(mom)
            impact = mom * (1.0 + 2.0 * np.abs(acc)) * (1.0 + np.abs(corr))

            # ══ COMPONENT 4: Contagion (how many edges are non-IDLE) ══
            n_active = np.sum(p_avg[j, :, S_IDLE] < 0.5)
            contagion = np.exp(n_active / N_EDGES)

            # ══ STRUCTURAL RESONANCE: combine all 4 components ══
            # Base: net pressure × impact × contagion (original)
            base_sr = np.mean(net_pressure * np.abs(impact)) * contagion

            # Boost: transition rate × direction (new — captures lifecycle DYNAMICS)
            # When many edges transition toward fear simultaneously → strong signal
            transition_boost = transition_rate * net_transition_direction * 2.0

            sr = np.tanh((base_sr + transition_boost) * 0.3) * 100
            sr_raw[i + j] = sr

    # Normalize to 0-100
    p2 = np.percentile(sr_raw, 2)
    p98 = np.percentile(sr_raw, 98)
    sr_range = max(p98 - p2, 1e-8)
    sr_norm = np.clip((sr_raw - p2) / sr_range * 100.0, 0, 100)

    # CFI = 100 - SR (high SR = fear -> low CFI)
    cfi_raw = 100.0 - sr_norm

    # Smooth with EMA-7
    cfi_smooth = pd.Series(cfi_raw).ewm(span=14).mean().values
    all_edge_probs = np.concatenate(all_edge_probs, axis=0)

    print(f"[CFI] SR raw range: [{sr_raw.min():.4f}, {sr_raw.max():.4f}]")
    print(f"[CFI] CFI raw: [{cfi_raw.min():.1f}, {cfi_raw.max():.1f}], std={cfi_raw.std():.1f}")
    print(f"[CFI] Smooth:  [{cfi_smooth.min():.1f}, {cfi_smooth.max():.1f}], std={cfi_smooth.std():.1f}")
    return cfi_raw, cfi_smooth, all_edge_probs


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 6 — ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

def find_crossing(series, threshold, direction="below", sustained=3):
    """Find first date where series crosses threshold for >=sustained days."""
    if direction == "below":
        cond = series < threshold
        above = series >= threshold
    else:
        cond = series > threshold
        above = series <= threshold

    was_above = False
    count = 0
    for i in range(len(series)):
        val = series.iloc[i]
        if pd.isna(val):
            continue
        if not was_above:
            if above.iloc[i]:
                was_above = True
            continue
        if cond.iloc[i]:
            count += 1
            if count >= sustained:
                return series.index[i - sustained + 1]
        else:
            count = 0
    return None


def granger_test(x, y, maxlag):
    """Granger-style F-test: does x help predict y beyond y's own lags?"""
    from numpy.linalg import lstsq
    n = len(x)
    if n < maxlag + 10:
        return 0.0, 1.0
    Y = y[maxlag:]
    X_full = np.column_stack(
        [y[maxlag - i - 1: n - i - 1] for i in range(maxlag)] +
        [x[maxlag - i - 1: n - i - 1] for i in range(maxlag)]
    )
    X_restricted = np.column_stack(
        [y[maxlag - i - 1: n - i - 1] for i in range(maxlag)]
    )
    X_full = np.column_stack([X_full, np.ones(len(Y))])
    X_restricted = np.column_stack([X_restricted, np.ones(len(Y))])

    b_full, _, _, _ = lstsq(X_full, Y, rcond=None)
    b_rest, _, _, _ = lstsq(X_restricted, Y, rcond=None)

    ss_full = np.sum((Y - X_full @ b_full) ** 2)
    ss_rest = np.sum((Y - X_restricted @ b_rest) ** 2)

    df1 = maxlag
    df2 = len(Y) - 2 * maxlag - 1
    if df2 <= 0 or ss_full <= 0:
        return 0.0, 1.0

    f_stat = ((ss_rest - ss_full) / df1) / (ss_full / df2)
    p_val = 1.0 - stats.f.cdf(f_stat, df1, df2)
    return f_stat, p_val


def run_birth_audit(model, edge_data, dates, edge_names):
    """Print BIRTH count trajectory around COVID (Dec 2019 - Mar 2020)."""
    print("\n" + "=" * 80)
    print("  BIRTH AUDIT: COVID-19 Period (Dec 2019 - Mar 2020)")
    print("=" * 80)

    seq_len = CFG["seq_len"]
    model.eval()

    # Build sequences for the audit window
    audit_start = pd.Timestamp("2019-12-01")
    audit_end = pd.Timestamp("2020-03-31")

    header = f"{'Date':>12}  {'BIRTH_n':>8}  {'REINF_n':>8}  {'IDLE_n':>8}  {'CFI':>6}"
    print(header)
    print("-" * len(header))

    for i in range(seq_len, len(edge_data)):
        d = dates[i]
        if d < audit_start or d > audit_end:
            continue

        x_seq = edge_data[i - seq_len:i][np.newaxis]  # [1, T, E, 8]
        x_t = torch.from_numpy(x_seq).to(DEVICE)
        with torch.no_grad():
            out = model(x_t)

        ep = out["edge_probs"][0, -1].numpy()  # [E, 5]
        # Count edges in each dominant state
        dominant = ep.argmax(axis=1)
        n_birth = (dominant == S_BIRTH).sum()
        n_reinf = (dominant == S_REINFORCE).sum()
        n_idle = (dominant == S_IDLE).sum()

        # Quick CFI (simplified — same logic as main compute_cfi)
        p = out["edge_probs"][0, -5:].mean(dim=0).numpy()  # [E, 5]
        x_last = x_seq[0, -5:].mean(axis=0)                # [E, 8]
        fear_p = p[:, S_BIRTH] * 2.0 + p[:, S_REINFORCE] * 3.0
        recov_p = p[:, S_DECAY] * 1.5 + p[:, S_DEATH] * 1.0
        net_p = fear_p - recov_p
        mom = x_last[:, 0]; acc = x_last[:, 1]
        corr = x_last[:, 4] if x_last.shape[-1] > 4 else np.zeros_like(mom)
        impact = mom * (1.0 + 2.0 * np.abs(acc)) * (1.0 + np.abs(corr))
        n_active = np.sum(p[:, S_IDLE] < 0.5)
        contagion = np.exp(n_active / N_EDGES)
        sr = np.tanh(np.mean(net_p * np.abs(impact)) * contagion * 0.3) * 100
        cfi_val = 100 - sr

        date_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10]
        print(f"{date_str:>12}  {n_birth:>5}/35  {n_reinf:>5}/35  {n_idle:>5}/35  {cfi_val:>6.1f}")


# ════════════════════════════════════════════════════════════════════════════
#  PHASE 7 — FIGURES
# ════════════════════════════════════════════════════════════════════════════

def setup_dark_style():
    plt.rcParams.update({
        "figure.facecolor": "#0d1117",
        "axes.facecolor": "#0d1117",
        "axes.edgecolor": "#30363d",
        "axes.labelcolor": "#c9d1d9",
        "text.color": "#c9d1d9",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
        "grid.color": "#21262d",
        "legend.facecolor": "#161b22",
        "legend.edgecolor": "#30363d",
        "font.size": 11,
    })


def fig_cfi_overlay(dates_cfi, cfi_smooth, fng_df, fig_dir):
    """fig5_cfi_overlay.png — CFI vs CNN F&G with annotations."""
    setup_dark_style()
    fig, ax = plt.subplots(figsize=(16, 6))

    ax.plot(dates_cfi, cfi_smooth, color="#58a6ff", linewidth=1.2,
            label="CFI (EMA-7)", zorder=3)

    fng_aligned = fng_df.reindex(dates_cfi).interpolate(limit=5)
    if "fng" in fng_aligned.columns:
        fng_vals = fng_aligned["fng"].values
    else:
        fng_vals = fng_aligned.values.flatten()
    valid_mask = ~np.isnan(fng_vals.astype(float))
    ax.plot(dates_cfi[valid_mask], fng_vals[valid_mask], color="#f0883e",
            linewidth=1.0, alpha=0.7, label="CNN Fear & Greed")

    ax.axhspan(0, 25, color="#da3633", alpha=0.08)
    ax.axhspan(75, 100, color="#3fb950", alpha=0.08)
    ax.axhline(40, color="#da3633", linewidth=0.8, linestyle="--", alpha=0.5,
               label="Fear threshold (40)")

    # COVID early warning detection
    cfi_series = pd.Series(cfi_smooth, index=dates_cfi)
    fng_series = pd.Series(fng_vals.astype(float), index=dates_cfi)

    covid_window = (dates_cfi >= pd.Timestamp("2020-01-01")) & \
                   (dates_cfi <= pd.Timestamp("2020-04-01"))
    cfi_covid = cfi_series[covid_window]
    fng_covid = fng_series[covid_window].dropna()

    cfi_cross = find_crossing(cfi_covid, 40, "below", sustained=3)
    fng_cross = find_crossing(fng_covid, 40, "below", sustained=3)

    if cfi_cross is not None:
        ax.axvline(cfi_cross, color="#58a6ff", linewidth=1.5, linestyle=":", alpha=0.8)
        ax.annotate(f"CFI\n{cfi_cross.strftime('%Y-%m-%d')}", xy=(cfi_cross, 35),
                    fontsize=8, color="#58a6ff", ha="right",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#161b22", ec="#58a6ff", alpha=0.8))
    if fng_cross is not None:
        ax.axvline(fng_cross, color="#f0883e", linewidth=1.5, linestyle=":", alpha=0.8)
        ax.annotate(f"F&G\n{fng_cross.strftime('%Y-%m-%d')}", xy=(fng_cross, 30),
                    fontsize=8, color="#f0883e", ha="left",
                    bbox=dict(boxstyle="round,pad=0.3", fc="#161b22", ec="#f0883e", alpha=0.8))
    if cfi_cross is not None and fng_cross is not None:
        lead = (fng_cross - cfi_cross).days
        mid = cfi_cross + (fng_cross - cfi_cross) / 2
        ax.annotate(f"COVID-19: CFI leads by {lead} days",
                    xy=(mid, 20), fontsize=10, color="#f85149", fontweight="bold",
                    ha="center",
                    bbox=dict(boxstyle="round,pad=0.4", fc="#161b22", ec="#f85149", alpha=0.9))

    # Aug 2024 — removed (flash crash, CFI lags on sudden events)

    ax.set_ylim(0, 100)
    ax.set_ylabel("Index Value")
    ax.set_title("KAIROS V4 Causal Fear Index vs CNN Fear & Greed Index",
                 fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = os.path.join(fig_dir, "fig5_cfi_overlay.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] Saved {path}")
    return cfi_cross, fng_cross


def fig_covid_zoom(dates_cfi, cfi_smooth, fng_df, cfi_cross, fng_cross, fig_dir):
    """fig3_covid_zoom.png — Jan-Apr 2020 zoom."""
    setup_dark_style()
    mask = (dates_cfi >= pd.Timestamp("2020-01-01")) & \
           (dates_cfi <= pd.Timestamp("2020-04-30"))
    d = dates_cfi[mask]
    c = cfi_smooth[mask]

    fng_aligned = fng_df.reindex(d).interpolate(limit=5)
    fng_vals = fng_aligned["fng"].values if "fng" in fng_aligned.columns \
               else fng_aligned.values.flatten()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(d, c, color="#58a6ff", linewidth=2, label="CFI (EMA-7)")
    valid_mask = ~np.isnan(fng_vals.astype(float))
    ax.plot(d[valid_mask], fng_vals[valid_mask], color="#f0883e",
            linewidth=1.5, label="CNN Fear & Greed")

    ax.axhspan(0, 25, color="#da3633", alpha=0.1)
    ax.axhline(40, color="#da3633", linewidth=0.8, linestyle="--", alpha=0.5)

    if cfi_cross is not None:
        ax.axvline(cfi_cross, color="#58a6ff", linewidth=2, linestyle="--", alpha=0.9)
        ax.annotate(f"CFI alarm\n{cfi_cross.strftime('%m-%d')}", xy=(cfi_cross, 42),
                    fontsize=10, color="#58a6ff", fontweight="bold", ha="right")
    if fng_cross is not None:
        ax.axvline(fng_cross, color="#f0883e", linewidth=2, linestyle="--", alpha=0.9)
        ax.annotate(f"F&G alarm\n{fng_cross.strftime('%m-%d')}", xy=(fng_cross, 42),
                    fontsize=10, color="#f0883e", fontweight="bold", ha="left")
    if cfi_cross is not None and fng_cross is not None:
        lead = (fng_cross - cfi_cross).days
        mid_y = 85
        ax.annotate("", xy=(fng_cross, mid_y), xytext=(cfi_cross, mid_y),
                    arrowprops=dict(arrowstyle="<->", color="#f85149", lw=2))
        mid_x = cfi_cross + (fng_cross - cfi_cross) / 2
        ax.text(mid_x, mid_y + 3, f"{lead} days early", ha="center", fontsize=11,
                color="#f85149", fontweight="bold")

    ax.set_ylim(0, 100)
    ax.set_title("COVID-19 Crash: Early Detection Zoom (Jan-Apr 2020)",
                 fontsize=13, fontweight="bold")
    ax.legend(loc="lower left", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = os.path.join(fig_dir, "fig3_covid_zoom.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] Saved {path}")


def fig_fsm_dynamics(dates_cfi, all_edge_probs, X_all, edge_names, fig_dir):
    """fig4_fsm_dynamics.png — CSM state dynamics + edge importance."""
    setup_dark_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[2, 1])

    # Top: rolling 60-day mean of CSM state probabilities
    ep_last = all_edge_probs[:, -1]   # [N, E, 5]
    state_means = ep_last.mean(axis=1) # [N, 5]

    colors_states = ["#8b949e", "#58a6ff", "#f85149", "#d2a8ff", "#484f58"]
    window = 60
    for si in range(5):
        rolled = pd.Series(state_means[:, si]).rolling(window, min_periods=10).mean().values
        ax1.plot(dates_cfi, rolled, color=colors_states[si], linewidth=1.5,
                 label=STATE_NAMES[si])
    ax1.set_ylabel("Mean State Probability")
    ax1.set_title("CSM State Dynamics (60-day Rolling Mean)", fontsize=12, fontweight="bold")
    ax1.legend(ncol=5, loc="upper right", fontsize=8)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.grid(True, alpha=0.3)

    # Bottom: top-10 edges by mean activity
    edge_activity = np.mean(np.abs(X_all[:, -1, :, 0]) + np.abs(X_all[:, -1, :, 1]), axis=0)
    short_names = []
    for en in edge_names:
        parts = en.split("->")
        short_names.append(f"{parts[0][:8]}->{parts[1][:8]}")
    top10_idx = np.argsort(edge_activity)[-10:][::-1]
    top10_names = [short_names[i] for i in top10_idx]
    top10_vals = edge_activity[top10_idx]

    ax2.barh(range(10), top10_vals[::-1], color="#58a6ff", alpha=0.8)
    ax2.set_yticks(range(10))
    ax2.set_yticklabels(top10_names[::-1], fontsize=8)
    ax2.set_xlabel("Mean Edge Activity")
    ax2.set_title("Top-10 Macro Edges by Activity", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="x")

    fig.tight_layout()
    path = os.path.join(fig_dir, "fig4_fsm_dynamics.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] Saved {path}")


def fig_granger(dates_cfi, cfi_smooth, fng_df, fig_dir):
    """fig5_granger_analysis.png — Cross-correlation + Granger tests."""
    setup_dark_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    cfi_s = pd.Series(cfi_smooth, index=dates_cfi)
    fng_s = fng_df.reindex(dates_cfi)
    if hasattr(fng_s, "columns"):
        fng_s = fng_s.iloc[:, 0]
    common = cfi_s.dropna().index.intersection(fng_s.dropna().index)
    c = cfi_s.loc[common].values.astype(float)
    f_arr = fng_s.loc[common].values.astype(float)

    # Cross-correlation
    max_lag = 20
    lags = range(-max_lag, max_lag + 1)
    xcorr = []
    for lag in lags:
        if lag >= 0:
            c_slice = c[:len(c) - lag] if lag > 0 else c
            f_slice = f_arr[lag:] if lag > 0 else f_arr
        else:
            c_slice = c[-lag:]
            f_slice = f_arr[:len(f_arr) + lag]
        if len(c_slice) > 10:
            xcorr.append(np.corrcoef(c_slice, f_slice)[0, 1])
        else:
            xcorr.append(0.0)

    ax1.bar(list(lags), xcorr, color="#58a6ff", alpha=0.7, width=0.8)
    best_lag = list(lags)[np.argmax(xcorr)]
    ax1.axvline(best_lag, color="#f85149", linestyle="--", linewidth=1.5)
    ax1.annotate(f"Peak at lag={best_lag}", xy=(best_lag, max(xcorr)),
                 fontsize=9, color="#f85149",
                 ha="left" if best_lag >= 0 else "right")
    ax1.set_xlabel("Lag (days, positive = CFI leads)")
    ax1.set_ylabel("Pearson Correlation")
    ax1.set_title("(a) Cross-Correlation: CFI vs F&G", fontsize=11, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    # Granger p-values
    test_lags = [1, 3, 5, 10, 15, 20]
    p_cfi_to_fg = []
    p_fg_to_cfi = []
    f_cfi_to_fg = []
    f_fg_to_cfi = []
    for lag in test_lags:
        f1, p1 = granger_test(c, f_arr, lag)
        f2, p2 = granger_test(f_arr, c, lag)
        p_cfi_to_fg.append(p1)
        p_fg_to_cfi.append(p2)
        f_cfi_to_fg.append(f1)
        f_fg_to_cfi.append(f2)

    x_pos = np.arange(len(test_lags))
    w = 0.35
    ax2.bar(x_pos - w / 2, p_cfi_to_fg, w, color="#58a6ff", alpha=0.8, label="CFI -> F&G")
    ax2.bar(x_pos + w / 2, p_fg_to_cfi, w, color="#f0883e", alpha=0.8, label="F&G -> CFI")
    ax2.axhline(0.05, color="#f85149", linestyle="--", linewidth=1, label="p=0.05")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([str(l) for l in test_lags])
    ax2.set_xlabel("Lag (days)")
    ax2.set_ylabel("p-value")
    ax2.set_title("(b) Granger Causality p-values", fontsize=11, fontweight="bold")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale("log")

    fig.tight_layout()
    path = os.path.join(fig_dir, "fig5_granger_analysis.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] Saved {path}")

    return test_lags, f_cfi_to_fg, p_cfi_to_fg, f_fg_to_cfi, p_fg_to_cfi


def fig_training(history, fig_dir):
    """fig6_training_performance.png — Loss + val accuracy."""
    setup_dark_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    epochs = range(1, len(history["train_loss"]) + 1)

    ax1.plot(epochs, history["train_loss"], color="#58a6ff", linewidth=1.5)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Unified Loss")
    ax1.set_title("(a) Training Loss", fontsize=11, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    ax2.plot(epochs, [v * 100 for v in history["val_bacc"]], color="#3fb950", linewidth=1.5)
    best_ep = np.argmax(history["val_bacc"]) + 1
    best_val = max(history["val_bacc"]) * 100
    ax2.axvline(best_ep, color="#f85149", linestyle="--", alpha=0.7)
    ax2.annotate(f"Best: {best_val:.1f}% @ ep {best_ep}", xy=(best_ep, best_val),
                 fontsize=9, color="#f85149",
                 xytext=(best_ep + 5, best_val - 3),
                 arrowprops=dict(arrowstyle="->", color="#f85149"))
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Balanced Accuracy (%)")
    ax2.set_title("(b) Validation Balanced Accuracy", fontsize=11, fontweight="bold")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    path = os.path.join(fig_dir, "fig6_training_performance.png")
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIG] Saved {path}")


# ════════════════════════════════════════════════════════════════════════════
#  MAIN — FULL PIPELINE
# ════════════════════════════════════════════════════════════════════════════

def main():
    set_seed(SEED)
    os.makedirs(FIG_DIR, exist_ok=True)
    print("=" * 80)
    print("  KAIROS V4 — Symbolic Resonance GNN (Correlation-Based Edge Features)")
    print("  Cap-Weighted Clusters | 8D Edge Features | Cross-Edge Attention")
    print("=" * 80)

    # ── 1. Data Pipeline ────────────────────────────────────────────────────
    prices = download_market_data()
    z_on, z_off, median_prices = build_clusters_cap_weighted(prices)
    edge_data, dates, edge_names = build_edge_features(z_on, z_off, median_prices)
    labels = make_pseudo_labels(z_on)
    edge_states = make_edge_state_labels(edge_data)

    # Align lengths
    min_len = min(len(edge_data), len(labels), len(edge_states))
    edge_data = edge_data[:min_len]
    labels = labels[:min_len]
    edge_states = edge_states[:min_len]
    dates = dates[:min_len]

    X, Y, ES = create_sequences(edge_data, labels, edge_states, seq_len=CFG["seq_len"])

    # Dates for each sequence (date of last element)
    dates_seq = dates[CFG["seq_len"]:]
    dates_seq = dates_seq[:len(Y)]  # align

    # ── 2. Fetch F&G ────────────────────────────────────────────────────────
    fng_df = fetch_fear_greed()

    # ── 3. Train ────────────────────────────────────────────────────────────
    model, history, val_bacc, test_bacc, splits = train_model(X, Y, dates_seq, ES=ES)

    # ── 4. CFI ──────────────────────────────────────────────────────────────
    cfi_raw, cfi_smooth, all_edge_probs = compute_cfi(model, X)

    # ── 5. BIRTH Audit ──────────────────────────────────────────────────────
    run_birth_audit(model, edge_data, dates, edge_names)

    # ── 6. CSM State Distribution ───────────────────────────────────────────
    ep_last = all_edge_probs[:, -1]  # [N, E, 5]
    dominant_states = ep_last.argmax(axis=-1)  # [N, E]
    print("\n[CSM] State distribution (dominant state across all samples & edges):")
    for si, sn in enumerate(STATE_NAMES):
        pct = 100 * (dominant_states == si).mean()
        print(f"  {sn:>12}: {pct:.1f}%")

    # ── 7. Figures ──────────────────────────────────────────────────────────
    dates_cfi = dates_seq[:len(cfi_smooth)]

    print("\n[FIGURES] Generating publication figures ...")
    cfi_cross, fng_cross = fig_cfi_overlay(dates_cfi, cfi_smooth, fng_df, FIG_DIR)
    fig_covid_zoom(dates_cfi, cfi_smooth, fng_df, cfi_cross, fng_cross, FIG_DIR)
    fig_fsm_dynamics(dates_cfi, all_edge_probs, X, edge_names, FIG_DIR)
    granger_results = fig_granger(dates_cfi, cfi_smooth, fng_df, FIG_DIR)
    fig_training(history, FIG_DIR)

    # ── 8. Granger Summary ──────────────────────────────────────────────────
    test_lags, f_cfi_fg, p_cfi_fg, f_fg_cfi, p_fg_cfi = granger_results

    print("\n[GRANGER] Granger Causality Tests:")
    print(f"  {'Lag':>5}  {'CFI->F&G F':>12}  {'p-val':>10}  {'F&G->CFI F':>12}  {'p-val':>10}")
    for i, lag in enumerate(test_lags):
        print(f"  {lag:>5}  {f_cfi_fg[i]:>12.3f}  {p_cfi_fg[i]:>10.5f}  "
              f"{f_fg_cfi[i]:>12.3f}  {p_fg_cfi[i]:>10.5f}")

    # ── 9. COVID Lead ───────────────────────────────────────────────────────
    covid_lead = None
    if cfi_cross is not None and fng_cross is not None:
        covid_lead = (fng_cross - cfi_cross).days

    # ── 10. Final Summary ───────────────────────────────────────────────────
    birth_rate = 100 * (dominant_states == S_BIRTH).mean()
    reinf_rate = 100 * (dominant_states == S_REINFORCE).mean()

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print("\n" + "=" * 80)
    print("  KAIROS V4 Results")
    print("=" * 80)
    print(f"  Parameters:       {n_params:,}")
    print(f"  BIRTH rate:       {birth_rate:.1f}% (target: 3-8%)")
    print(f"  REINFORCE rate:   {reinf_rate:.1f}%")
    print(f"  Val acc:          {val_bacc*100:.2f}%")
    print(f"  Test acc:         {test_bacc*100:.2f}%")
    print(f"  CFI range:        [{cfi_smooth.min():.1f}, {cfi_smooth.max():.1f}], std={cfi_smooth.std():.1f}")

    if covid_lead is not None:
        cfi_str = cfi_cross.strftime("%Y-%m-%d") if cfi_cross else "N/A"
        fng_str = fng_cross.strftime("%Y-%m-%d") if fng_cross else "N/A"
        print(f"  COVID:            CFI cross={cfi_str}, F&G cross={fng_str}, lead=+{covid_lead} days")
    else:
        print(f"  COVID:            Could not detect crossing (check CFI dynamics)")

    # Granger at lag 10
    idx10 = test_lags.index(10) if 10 in test_lags else -1
    if idx10 >= 0:
        print(f"  Granger CFI->F&G lag 10: F={f_cfi_fg[idx10]:.3f}, p={p_cfi_fg[idx10]:.5f}")
        print(f"  Granger F&G->CFI lag 10: F={f_fg_cfi[idx10]:.3f}, p={p_fg_cfi[idx10]:.5f}")

    print(f"\n  Figures saved to: {FIG_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
