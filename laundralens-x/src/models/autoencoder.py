"""
LaundraLens X — Autoencoder Anomaly Detector (PyTorch)
Trained on normal behavior. High reconstruction error = anomalous.
Includes documented fallback if training is unstable.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from sklearn.preprocessing import StandardScaler

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class _Autoencoder(nn.Module if TORCH_AVAILABLE else object):
    """Simple symmetric autoencoder: Input → 64 → 32 → 16 → 32 → 64 → Output"""
    def __init__(self, input_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
        )
        self.decoder = nn.Sequential(
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, input_dim),
        )

    def forward(self, x):
        latent = self.encoder(x)
        return self.decoder(latent)


class AutoencoderDetector:
    """PyTorch autoencoder-based anomaly detector."""

    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.model: Optional[_Autoencoder] = None
        self.scaler: Optional[StandardScaler] = None
        self._threshold: float = 0.0
        self._error_max: float = 1.0
        self._fallback: bool = False
        self.input_dim: int = 0

    def train(
        self,
        X_normal: np.ndarray,
        epochs: int = 50,
        batch_size: int = 64,
        lr: float = 1e-3,
    ) -> dict:
        """
        Train autoencoder on normal-account features.
        If training fails or is unstable, activates documented fallback.
        """
        if not TORCH_AVAILABLE:
            print("    [WARN] PyTorch not available — autoencoder using fallback.")
            self._fallback = True
            return {"fallback": True, "reason": "PyTorch not available"}

        try:
            # Scale
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X_normal).astype(np.float32)
            self.input_dim = X_scaled.shape[1]

            # Model
            self.model = _Autoencoder(self.input_dim)
            optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-5)
            criterion = nn.MSELoss()
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

            # DataLoader
            tensor = torch.FloatTensor(X_scaled)
            dataset = TensorDataset(tensor, tensor)
            loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

            self.model.train()
            losses = []
            for epoch in range(epochs):
                epoch_loss = 0.0
                for batch_x, batch_y in loader:
                    optimizer.zero_grad()
                    out = self.model(batch_x)
                    loss = criterion(out, batch_y)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()
                avg_loss = epoch_loss / len(loader)
                losses.append(avg_loss)
                scheduler.step(avg_loss)

            # Check for training instability
            if losses[-1] > losses[0] * 2 or np.isnan(losses[-1]):
                print("    [WARN] Autoencoder training unstable — activating fallback.")
                self._fallback = True
                return {"fallback": True, "reason": "Training instability detected", "final_loss": losses[-1]}

            # Calibrate threshold on normal data
            errors = self._compute_errors_batch(X_scaled)
            self._threshold = float(np.percentile(errors, 95))
            self._error_max = float(np.percentile(errors, 99.9))

            return {
                "fallback": False,
                "epochs": epochs,
                "final_loss": round(float(losses[-1]), 6),
                "reconstruction_threshold_95pct": round(self._threshold, 6),
                "n_normal_samples": len(X_normal),
            }

        except Exception as e:
            print(f"    [WARN] Autoencoder training failed: {e} — activating fallback.")
            self._fallback = True
            return {"fallback": True, "reason": str(e)}

    def _compute_errors_batch(self, X_scaled: np.ndarray) -> np.ndarray:
        """Compute reconstruction errors for a batch."""
        self.model.eval()
        with torch.no_grad():
            tensor = torch.FloatTensor(X_scaled)
            out = self.model(tensor)
            errors = torch.mean((tensor - out) ** 2, dim=1).numpy()
        return errors

    def predict_score(self, X: np.ndarray) -> float:
        """
        Return normalized anomaly score [0,1].
        0 = normal reconstruction, 1 = high reconstruction error.
        """
        if self._fallback or self.model is None:
            return 0.5  # documented neutral fallback

        if self.scaler is None:
            return 0.5

        try:
            X_scaled = self.scaler.transform(X.reshape(1, -1)).astype(np.float32)
            errors = self._compute_errors_batch(X_scaled)
            raw_error = float(errors[0])

            # Normalize to [0,1] using training-set max error
            normalized = raw_error / (self._error_max + 1e-8)
            return round(float(np.clip(normalized, 0.0, 1.0)), 4)
        except Exception:
            return 0.5

    def save(self):
        if not self._fallback and self.model is not None:
            torch.save(self.model.state_dict(), self.artifact_dir / "model.pt")
        with open(self.artifact_dir / "scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)
        meta = {
            "fallback": self._fallback,
            "threshold": self._threshold,
            "error_max": self._error_max,
            "input_dim": self.input_dim,
        }
        with open(self.artifact_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)
        print(f"    Autoencoder artifacts saved to {self.artifact_dir}/ (fallback={self._fallback})")

    @classmethod
    def load(cls, artifact_dir: Path) -> "AutoencoderDetector":
        detector = cls(artifact_dir)
        meta_path = artifact_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            detector._fallback = meta.get("fallback", True)
            detector._threshold = meta.get("threshold", 0.0)
            detector._error_max = meta.get("error_max", 1.0)
            detector.input_dim = meta.get("input_dim", 0)

        if not detector._fallback and TORCH_AVAILABLE:
            model_path = artifact_dir / "model.pt"
            if model_path.exists() and detector.input_dim > 0:
                detector.model = _Autoencoder(detector.input_dim)
                detector.model.load_state_dict(
                    torch.load(model_path, map_location="cpu", weights_only=True)
                )
                detector.model.eval()

        scaler_path = artifact_dir / "scaler.pkl"
        if scaler_path.exists():
            with open(scaler_path, "rb") as f:
                detector.scaler = pickle.load(f)

        return detector
