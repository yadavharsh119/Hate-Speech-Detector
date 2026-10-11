"""
Central configuration for the moderation backend.

Switching models (DistilBERT <-> ANN) is a ONE-LINE change: edit MODEL_TYPE
below, or set the MODEL_TYPE environment variable. Nothing else in the
codebase needs to change.
"""

import os

# ---------------------------------------------------------------------------
# Which trained model to load. "distilbert" is the default since it's the
# more accurate model (89% acc / 0.77 macro F1 vs the ANN's 81% / 0.65).
# Set env var MODEL_TYPE=ann to use the smaller/faster ANN instead.
# ---------------------------------------------------------------------------
MODEL_TYPE = os.getenv("MODEL_TYPE", "distilbert")  # "distilbert" | "ann"

# ---------------------------------------------------------------------------
# Where the trained artifacts live on disk. These folders are intentionally
# NOT in git (see .gitignore) — they're shared separately (Drive / HF Hub)
# since the DistilBERT folder alone is ~500MB+.
# ---------------------------------------------------------------------------
DISTILBERT_MODEL_PATH = os.getenv("DISTILBERT_MODEL_PATH", "model/distilbert_final")

ANN_MODEL_DIR = os.getenv("ANN_MODEL_DIR", "model/ann")
ANN_WEIGHTS_FILE = os.getenv("ANN_WEIGHTS_FILE", "ann_model_final.pt")
ANN_TFIDF_FILE = os.getenv("ANN_TFIDF_FILE", "tfidf_vectorizer.pkl")
ANN_LABEL_ENCODER_FILE = os.getenv("ANN_LABEL_ENCODER_FILE", "label_encoder.pkl")
ANN_HIDDEN_SIZE = int(os.getenv("ANN_HIDDEN_SIZE", "128"))
ANN_DROPOUT = float(os.getenv("ANN_DROPOUT", "0.3"))

# Must match training: DistilBERT was tokenized/trained at this max length.
MAX_SEQ_LENGTH = int(os.getenv("MAX_SEQ_LENGTH", "128"))

# ---------------------------------------------------------------------------
# Class mapping: internal training labels -> public-facing severity names.
# The trained models output {hate, offensive, safe, threat} in this fixed
# alphabetical order (that's how sklearn's LabelEncoder sorted them during
# training) — do not reorder this without re-checking the label_encoder.
# ---------------------------------------------------------------------------
TRAINING_CLASSES_ORDER = ["hate", "offensive", "safe", "threat"]  # alphabetical, matches LabelEncoder

LABEL_DISPLAY_MAP = {
    "safe": None,          # no severity label for clean content
    "offensive": "Mild",
    "hate": "Moderate",
    "threat": "Severe",
}