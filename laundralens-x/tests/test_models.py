"""
Unit tests for Machine Learning Detection Models and ModelRegistry.
"""
import numpy as np
import pytest
from src.models.model_registry import registry
from src.features.pipeline import ML_FEATURE_NAMES


def test_model_registry_loaded():
    status = registry.load_all()
    assert isinstance(status, dict)
    assert registry.models_loaded is True


def test_model_inference():
    # Test sample with 39 features
    x = [0.5] * len(ML_FEATURE_NAMES)
    scores = registry.score_all(x)
    assert "xgboost_score" in scores
    assert "isolation_score" in scores
    assert "autoencoder_score" in scores

    for name, score in scores.items():
        assert 0.0 <= score <= 1.0


def test_shap_explanation():
    x = [0.5] * len(ML_FEATURE_NAMES)
    shap_vals = registry.get_shap_values(x)
    assert isinstance(shap_vals, dict)
