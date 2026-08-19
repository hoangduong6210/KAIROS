#!/usr/bin/env python3
"""Run the frozen KAIROS benchmark protocol and emit complete atomic records."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kairos import model as canonical  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


class GRUBaseline(nn.Module):
    def __init__(self, feature_count: int, hidden: int = 48) -> None:
        super().__init__()
        self.encoder = nn.Linear(feature_count, hidden)
        self.gru = nn.GRU(hidden, hidden, batch_first=True)
        self.head = nn.Linear(hidden, 2)

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        temporal = self.encoder(x.mean(dim=2))
        encoded, _ = self.gru(temporal)
        return {"probs": F.softmax(self.head(encoded[:, -1]), dim=-1)}


class MLPBaseline(nn.Module):
    def __init__(self, edge_count: int, feature_count: int, hidden: int = 48) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(edge_count * feature_count, hidden),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(hidden, 2),
        )

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        latest = x[:, -1].flatten(start_dim=1)
        return {"probs": F.softmax(self.net(latest), dim=-1)}


@dataclass(frozen=True)
class DatasetBundle:
    train: tuple[torch.Tensor, torch.Tensor]
    validation: tuple[torch.Tensor, torch.Tensor]
    test: tuple[torch.Tensor, torch.Tensor]
    metadata: dict[str, object]


def _forward_drops(z_on: pd.DataFrame, horizon: int, smoothing: int) -> np.ndarray:
    signal = z_on.mean(axis=1).rolling(smoothing, min_periods=1).mean().to_numpy()
    drops = np.full(len(signal), np.nan, dtype=np.float64)
    for index in range(len(signal) - horizon):
        drops[index] = signal[index] - np.min(signal[index + 1 : index + 1 + horizon])
    return drops


def build_dataset(config: dict[str, object]) -> DatasetBundle:
    study = config["study"]
    split = config["split"]
    target = config["target"]
    data_path = ROOT / str(study["data_file"])
    observed_hash = sha256(data_path)
    if observed_hash != study["data_sha256"]:
        raise ValueError(f"data checksum mismatch: {observed_hash}")

    prices = pd.read_csv(data_path, index_col="Date", parse_dates=True)
    prices = prices.sort_index()
    z_on, z_off, median_prices = canonical.build_clusters_cap_weighted(prices)
    features, dates, _edge_names = canonical.build_edge_features(z_on, z_off, median_prices)

    sequence_length = int(split["sequence_length"])
    horizon = int(split["forecast_horizon"])
    drops = _forward_drops(z_on, horizon, int(target["smoothing_window"]))
    train_end = pd.Timestamp(str(split["train_end"]))
    validation_end = pd.Timestamp(str(split["validation_end"]))

    positions = np.arange(sequence_length - 1, len(dates) - horizon)
    target_dates = pd.DatetimeIndex(dates[positions])
    horizon_dates = pd.DatetimeIndex(dates[positions + horizon])
    train_mask = (target_dates <= train_end) & (horizon_dates <= train_end)
    validation_mask = (
        (target_dates > train_end)
        & (target_dates <= validation_end)
        & (horizon_dates <= validation_end)
    )
    test_mask = target_dates > validation_end

    train_drops = drops[positions[train_mask]]
    positive_train_drops = train_drops[train_drops > 0]
    percentile_threshold = float(
        np.percentile(positive_train_drops, float(target["training_percentile"]))
    )
    threshold = max(float(target["minimum_drop"]), percentile_threshold)
    labels = (drops > threshold).astype(np.int64)
    windows = np.stack(
        [features[index - sequence_length + 1 : index + 1] for index in positions]
    ).astype(np.float32)
    outcomes = labels[positions]

    def tensors(mask: np.ndarray) -> tuple[torch.Tensor, torch.Tensor]:
        return torch.from_numpy(windows[mask]), torch.from_numpy(outcomes[mask])

    partitions = {
        "train": train_mask,
        "validation": validation_mask,
        "test": test_mask,
    }
    for name, mask in partitions.items():
        classes = np.unique(outcomes[mask])
        if len(classes) != 2:
            raise ValueError(f"partition {name} does not contain both classes")

    return DatasetBundle(
        train=tensors(train_mask),
        validation=tensors(validation_mask),
        test=tensors(test_mask),
        metadata={
            "data_file": str(study["data_file"]),
            "data_sha256": observed_hash,
            "rows": int(len(prices)),
            "columns": int(len(prices.columns)),
            "date_start": str(prices.index.min().date()),
            "date_end": str(prices.index.max().date()),
            "edge_count": int(features.shape[1]),
            "feature_count": int(features.shape[2]),
            "label_threshold": threshold,
            "partition_sizes": {name: int(mask.sum()) for name, mask in partitions.items()},
            "positive_rates": {
                name: float(outcomes[mask].mean()) for name, mask in partitions.items()
            },
        },
    )


def _classification_loss(
    output: dict[str, torch.Tensor], labels: torch.Tensor, weights: torch.Tensor, config: dict[str, object]
) -> torch.Tensor:
    probabilities = output["probs"].clamp_min(1e-8)
    loss = F.nll_loss(probabilities.log(), labels, weight=weights)
    loss = loss + float(config["training"]["tip_weight"]) * output.get(
        "kl_loss", torch.zeros((), device=labels.device)
    )
    if "compliance" in output:
        loss = loss + float(config["training"]["compliance_weight"]) * (
            1.0 - output["compliance"]
        ).mean()
    return loss


def _predict(model: nn.Module, features: torch.Tensor, device: torch.device) -> np.ndarray:
    model.eval()
    outputs: list[torch.Tensor] = []
    with torch.no_grad():
        for batch in DataLoader(TensorDataset(features), batch_size=512, shuffle=False):
            outputs.append(model(batch[0].to(device))["probs"].cpu())
    return torch.cat(outputs).numpy()


def train_attempt(
    model: nn.Module,
    bundle: DatasetBundle,
    config: dict[str, object],
    seed: int,
    device: torch.device,
) -> tuple[nn.Module, dict[str, object]]:
    set_seed(seed)
    model = model.to(device)
    x_train, y_train = bundle.train
    x_validation, y_validation = bundle.validation
    counts = torch.bincount(y_train, minlength=2).float()
    weights = (counts.sum() / (2.0 * counts.clamp_min(1))).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["training"]["learning_rate"]),
        weight_decay=float(config["training"]["weight_decay"]),
    )
    loader = DataLoader(
        TensorDataset(x_train, y_train),
        batch_size=int(config["training"]["batch_size"]),
        shuffle=True,
        generator=torch.Generator().manual_seed(seed),
    )
    best_score = -math.inf
    best_state: dict[str, torch.Tensor] | None = None
    stale_epochs = 0
    epochs_run = 0
    started = time.monotonic()

    for epoch in range(int(config["training"]["epochs"])):
        epochs_run = epoch + 1
        model.train()
        for features, labels in loader:
            features = features.to(device)
            labels = labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = _classification_loss(model(features), labels, weights, config)
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite training loss")
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        validation_probabilities = _predict(model, x_validation, device)
        validation_prediction = validation_probabilities.argmax(axis=1)
        score = float(balanced_accuracy_score(y_validation.numpy(), validation_prediction))
        if score > best_score:
            best_score = score
            best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1
        if stale_epochs >= int(config["training"]["patience"]):
            break

    if best_state is None:
        raise RuntimeError("training did not produce a checkpoint")
    model.load_state_dict(best_state)
    return model, {
        "validation_balanced_accuracy": best_score,
        "epochs_run": epochs_run,
        "duration_seconds": time.monotonic() - started,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
    }


def evaluate(model: nn.Module, bundle: DatasetBundle, device: torch.device) -> dict[str, float]:
    features, labels = bundle.test
    probabilities = _predict(model, features, device)
    prediction = probabilities.argmax(axis=1)
    truth = labels.numpy()
    metrics = {
        "balanced_accuracy": float(balanced_accuracy_score(truth, prediction)),
        "f1": float(f1_score(truth, prediction, zero_division=0)),
        "roc_auc": float(roc_auc_score(truth, probabilities[:, 1])),
    }
    if not all(math.isfinite(value) for value in metrics.values()):
        raise FloatingPointError("non-finite evaluation metric")
    return metrics


def run(config_path: Path) -> dict[str, object]:
    with config_path.open(encoding="utf-8") as stream:
        config = json.load(stream)
    bundle = build_dataset(config)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    edge_count = int(bundle.metadata["edge_count"])
    feature_count = int(bundle.metadata["feature_count"])
    factories: dict[str, Callable[[], nn.Module]] = {
        "KAIROS": lambda: canonical.SRGNN(n_edges=edge_count, n_feat=feature_count),
        "GRU": lambda: GRUBaseline(feature_count=feature_count),
        "MLP": lambda: MLPBaseline(edge_count=edge_count, feature_count=feature_count),
    }
    attempts: list[dict[str, object]] = []
    for model_name in config["evaluation"]["models"]:
        for seed in config["training"]["seeds"]:
            record: dict[str, object] = {"model": model_name, "seed": int(seed)}
            try:
                set_seed(int(seed))
                model, training = train_attempt(
                    factories[model_name](), bundle, config, int(seed), device
                )
                record.update(status="success", training=training, metrics=evaluate(model, bundle, device))
            except Exception as exc:  # preserve every declared attempt before failing finalization
                record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
            attempts.append(record)

    expected = len(config["evaluation"]["models"]) * len(config["training"]["seeds"])
    successes = [attempt for attempt in attempts if attempt["status"] == "success"]
    complete = len(attempts) == expected and len(successes) == expected
    summary: dict[str, object] = {}
    if complete:
        for model_name in config["evaluation"]["models"]:
            records = [record for record in successes if record["model"] == model_name]
            summary[model_name] = {
                metric: {
                    "mean": float(np.mean([record["metrics"][metric] for record in records])),
                    "sample_std": float(np.std([record["metrics"][metric] for record in records], ddof=1)),
                }
                for metric in ("balanced_accuracy", "f1", "roc_auc")
            }

    return {
        "study_id": config["study"]["id"],
        "status": "complete" if complete else "failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "protocol": "protocols/benchmark-v1.md",
        "protocol_sha256": sha256(ROOT / "protocols/benchmark-v1.md"),
        "config": config_path.relative_to(ROOT).as_posix(),
        "config_sha256": sha256(config_path),
        "source": "src/kairos/model.py",
        "source_sha256": sha256(ROOT / "src/kairos/model.py"),
        "dataset": bundle.metadata,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "torch": torch.__version__,
            "device": str(device),
            "cuda": torch.version.cuda,
        },
        "expected_attempts": expected,
        "attempts": attempts,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/benchmark-v1.json")
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    result = run(config_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir = ROOT / str(config["study"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "result.json"
    partial_path = output_path.with_suffix(".json.partial")
    partial_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    os.replace(partial_path, output_path)
    print(json.dumps({"status": result["status"], "output": str(output_path)}, indent=2))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
