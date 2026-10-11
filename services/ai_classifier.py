import logging

logger = logging.getLogger("moderation.ai_classifier")

# Maps the four internal training labels that model_loader returns to the
# UI-facing category names that ingest_tweet stores in the DB.
_LABEL_TO_CATEGORY = {
    "safe":      "Clean",
    "offensive": "Mild",
    "hate":      "Moderate Hate",
    "threat":    "Severe",
}


def _fallback_predict(raw_text: str) -> dict:
    """
    Deterministic fallback used when model_loader is unavailable.
    Delegates to backend.fallback_classifier (same logic model_loader
    itself uses internally), then maps to UI categories.
    Never raises.
    """
    try:
        from backend.fallback_classifier import classify as fallback_classify
        label, confidence = fallback_classify(raw_text)
        category = _LABEL_TO_CATEGORY.get(label, "Clean")
    except Exception:
        logger.exception("fallback_classifier also failed; defaulting to Clean.")
        category, confidence = "Clean", 0.50

    return {
        "predicted_category": category,
        "confidence_score": round(confidence, 2),
        "flagged": category != "Clean",
        "model_source": "fallback",
    }


def predict_hate_speech(raw_text: str) -> dict:
    """
    AI inference interface called by ingest_tweet.

    Tries backend.model_loader.get_classifier() first (DistilBERT or ANN,
    depending on config.MODEL_TYPE).  If the model artifacts are missing
    model_loader already returns a FallbackClassifier transparently, so
    this layer only needs to handle unexpected exceptions.

    Returns:
    {
        "predicted_category": str,   # "Clean" | "Mild" | "Moderate Hate" | "Severe"
        "confidence_score":  float,  # 0.0 – 1.0
        "flagged":           bool,   # False iff Clean
        "model_source":      str,    # "distilbert" | "ann" | "fallback"
    }
    """
    try:
        from backend.model_loader import get_classifier
        from backend import config

        classifier = get_classifier()
        label, confidence = classifier.predict(raw_text)

        category = _LABEL_TO_CATEGORY.get(label, "Clean")

        # Determine which backend is actually running so callers can log it.
        classifier_type = type(classifier).__name__
        if "DistilBert" in classifier_type:
            source = "distilbert"
        elif "Ann" in classifier_type:
            source = "ann"
        else:
            source = "fallback"

        return {
            "predicted_category": category,
            "confidence_score": round(confidence, 2),
            "flagged": category != "Clean",
            "model_source": source,
        }

    except Exception:
        logger.exception(
            "model_loader raised an unexpected error; using deterministic fallback."
        )
        return _fallback_predict(raw_text)
