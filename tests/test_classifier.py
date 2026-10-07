"""
Tests for the model-loading integration layer.

- The fallback-classifier tests always run (no trained model needed) and
  confirm the pipeline works end-to-end right now.
- The real-model test is automatically SKIPPED (not failed) until the
  actual trained artifacts are dropped into place — this is intentional
  per the brief: "add a test that is skipped if the model folder is
  absent."
"""

import importlib
import os
from pathlib import Path

import pytest

from backend import config
from backend.fallback_classifier import classify as fallback_classify


# ---------------------------------------------------------------------------
# Fallback classifier — always runs, no artifacts required
# ---------------------------------------------------------------------------

def test_fallback_classifies_safe_text_as_safe():
    label, confidence = fallback_classify("Have a wonderful day, see you tomorrow!")
    assert label == "safe"
    assert 0.0 < confidence <= 1.0


def test_fallback_classifies_threat_text_as_threat():
    label, _ = fallback_classify("I will kill you if you post that again")
    assert label == "threat"


def test_fallback_classifies_hate_text_as_hate():
    label, _ = fallback_classify("People like you should not exist")
    assert label == "hate"


def test_fallback_classifies_offensive_text_as_offensive():
    label, _ = fallback_classify("You are such an idiot, shut up")
    assert label == "offensive"


def test_fallback_is_deterministic():
    """Same input must always give the same output — no randomness allowed."""
    text = "I will kill you"
    results = {fallback_classify(text) for _ in range(5)}
    assert len(results) == 1


def test_fallback_handles_empty_text():
    label, _ = fallback_classify("")
    assert label == "safe"


# ---------------------------------------------------------------------------
# get_classifier() falls back cleanly when no real model artifacts exist
# ---------------------------------------------------------------------------

def test_get_classifier_falls_back_when_artifacts_missing(monkeypatch, tmp_path):
    from backend import model_loader

    # Point config at empty, definitely-nonexistent paths
    monkeypatch.setattr(config, "DISTILBERT_MODEL_PATH", str(tmp_path / "no_such_distilbert"))
    monkeypatch.setattr(config, "ANN_MODEL_DIR", str(tmp_path / "no_such_ann"))
    monkeypatch.setattr(config, "MODEL_TYPE", "distilbert")

    model_loader.reset_classifier_for_testing()
    classifier = model_loader.get_classifier()

    assert isinstance(classifier, model_loader.FallbackClassifier)

    label, confidence = classifier.predict("I will kill you")
    assert label == "threat"

    model_loader.reset_classifier_for_testing()  # don't leak state into other tests


# ---------------------------------------------------------------------------
# Real trained model — SKIPPED automatically until artifacts are present
# ---------------------------------------------------------------------------

_distilbert_present = Path(config.DISTILBERT_MODEL_PATH).is_dir() and (
    any(Path(config.DISTILBERT_MODEL_PATH).glob("*.safetensors"))
    or (Path(config.DISTILBERT_MODEL_PATH) / "pytorch_model.bin").exists()
)


@pytest.mark.skipif(
    not _distilbert_present,
    reason=(
        "DistilBERT artifacts not found at config.DISTILBERT_MODEL_PATH "
        "(expected once Dhiraj's trained model folder is dropped in). "
        "Skipping real-model test, not failing the build."
    ),
)
def test_real_distilbert_model_loads_and_predicts():
    from backend import model_loader

    monkeypatch_module = pytest.MonkeyPatch()
    monkeypatch_module.setattr(config, "MODEL_TYPE", "distilbert")
    model_loader.reset_classifier_for_testing()

    classifier = model_loader.get_classifier()
    assert isinstance(classifier, model_loader.DistilBertClassifier)

    label, confidence = classifier.predict("Have a nice day!")
    assert label in {"hate", "offensive", "safe", "threat"}
    assert 0.0 <= confidence <= 1.0

    model_loader.reset_classifier_for_testing()
    monkeypatch_module.undo()
