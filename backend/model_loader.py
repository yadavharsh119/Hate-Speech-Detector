"""
Lazy-loaded classifier for the moderation backend.

Design goal: the REST of the app (FastAPI routes, CSP assignment, DB
writes) never needs to know whether we're using DistilBERT, the ANN, or
the rule-based fallback. Everything goes through `get_classifier()`,
which returns an object with a single method:

    classifier.predict(text: str) -> (label: str, confidence: float)

`label` is always one of the four internal training classes:
    "hate", "offensive", "safe", "threat"

Swapping DistilBERT <-> ANN is a one-line change in config.py
(MODEL_TYPE). If the configured model's artifact folder is missing, this
module logs a clear warning and transparently falls back to the
deterministic rule-based classifier so the API keeps working.
"""

import logging
import os
from pathlib import Path

from backend import config
from backend.fallback_classifier import classify as fallback_classify

logger = logging.getLogger("moderation.model_loader")

_classifier_instance = None  # module-level singleton, set on first use


class DistilBertClassifier:
    """Wraps a fine-tuned DistilBERT sequence-classification model."""

    def __init__(self, model_path: str):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        self._torch = torch

        # id2label from the model's own config, falling back to our fixed
        # training order if the config doesn't carry it (some save paths
        # only store {0: "LABEL_0", ...} placeholders).
        id2label = getattr(self.model.config, "id2label", None)
        if id2label and all(not str(v).startswith("LABEL_") for v in id2label.values()):
            self.id2label = {int(k): v for k, v in id2label.items()}
        else:
            self.id2label = dict(enumerate(config.TRAINING_CLASSES_ORDER))

        logger.info("Loaded DistilBERT classifier from %s on %s", model_path, self.device)

    def predict(self, text: str):
        torch = self._torch
        encodings = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=config.MAX_SEQ_LENGTH,
            return_tensors="pt",
        )
        input_ids = encodings["input_ids"].to(self.device)
        attention_mask = encodings["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=1)[0]
            pred_idx = int(torch.argmax(probs).item())
            confidence = float(probs[pred_idx].item())

        label = self.id2label[pred_idx]
        return label, confidence


class AnnClassifier:
    """Wraps the trained TF-IDF + feedforward ANN model."""

    def __init__(self, model_dir: str):
        import torch
        import torch.nn as nn
        import joblib

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._torch = torch

        weights_path = os.path.join(model_dir, config.ANN_WEIGHTS_FILE)
        tfidf_path = os.path.join(model_dir, config.ANN_TFIDF_FILE)
        label_encoder_path = os.path.join(model_dir, config.ANN_LABEL_ENCODER_FILE)

        self.tfidf = joblib.load(tfidf_path)
        self.label_encoder = joblib.load(label_encoder_path)

        class SimpleANN(nn.Module):
            def __init__(self, input_size, hidden_size, num_classes, dropout):
                super().__init__()
                self.fc1 = nn.Linear(input_size, hidden_size)
                self.relu1 = nn.ReLU()
                self.dropout1 = nn.Dropout(dropout)
                self.fc2 = nn.Linear(hidden_size, hidden_size)
                self.relu2 = nn.ReLU()
                self.dropout2 = nn.Dropout(dropout)
                self.fc3 = nn.Linear(hidden_size, num_classes)

            def forward(self, x):
                x = self.dropout1(self.relu1(self.fc1(x)))
                x = self.dropout2(self.relu2(self.fc2(x)))
                return self.fc3(x)

        input_size = len(self.tfidf.get_feature_names_out())
        num_classes = len(self.label_encoder.classes_)

        self.model = SimpleANN(input_size, config.ANN_HIDDEN_SIZE, num_classes, config.ANN_DROPOUT)
        self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        logger.info("Loaded ANN classifier from %s on %s", model_dir, self.device)

    def predict(self, text: str):
        import numpy as np
        torch = self._torch

        vec = self.tfidf.transform([text]).toarray().astype(np.float32)
        tensor = torch.tensor(vec).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]
            pred_idx = int(torch.argmax(probs).item())
            confidence = float(probs[pred_idx].item())

        label = self.label_encoder.classes_[pred_idx]
        return label, confidence


class FallbackClassifier:
    """Deterministic rule-based stand-in, used when no trained model is available."""

    def predict(self, text: str):
        return fallback_classify(text)


def _artifacts_present(model_type: str) -> bool:
    if model_type == "distilbert":
        path = Path(config.DISTILBERT_MODEL_PATH)
        return path.is_dir() and any(path.glob("*.safetensors")) or (path / "pytorch_model.bin").exists()
    if model_type == "ann":
        model_dir = Path(config.ANN_MODEL_DIR)
        required = [config.ANN_WEIGHTS_FILE, config.ANN_TFIDF_FILE, config.ANN_LABEL_ENCODER_FILE]
        return model_dir.is_dir() and all((model_dir / f).exists() for f in required)
    return False


def _build_classifier():
    model_type = config.MODEL_TYPE

    if not _artifacts_present(model_type):
        logger.warning(
            "Model artifacts for MODEL_TYPE=%r not found (looked in %r). "
            "Falling back to the deterministic rule-based classifier. "
            "This is NOT the trained model — accuracy will be much lower. "
            "Drop the real artifacts in place and restart to use the trained model.",
            model_type,
            config.DISTILBERT_MODEL_PATH if model_type == "distilbert" else config.ANN_MODEL_DIR,
        )
        return FallbackClassifier()

    try:
        if model_type == "distilbert":
            return DistilBertClassifier(config.DISTILBERT_MODEL_PATH)
        elif model_type == "ann":
            return AnnClassifier(config.ANN_MODEL_DIR)
        else:
            logger.warning("Unknown MODEL_TYPE=%r, using fallback classifier.", model_type)
            return FallbackClassifier()
    except Exception:
        logger.exception(
            "Failed to load %r model even though artifacts were found. "
            "Falling back to the rule-based classifier so the API stays up.",
            model_type,
        )
        return FallbackClassifier()


def get_classifier():
    """Returns the module-level classifier singleton, building it on first call."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = _build_classifier()
    return _classifier_instance


def reset_classifier_for_testing():
    """Test-only helper: clears the cached singleton so tests can reload cleanly."""
    global _classifier_instance
    _classifier_instance = None
