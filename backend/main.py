"""
FastAPI backend for the moderation system.

POST /predict
    Input:  {"text": "some social media text"}
    Output: {
        "internal_label": "hate",            # raw training class
        "category": "Moderate Hate",         # display label (config.LABEL_DISPLAY_MAP)
        "confidence": 0.92,
        "model_source": "distilbert"         # "distilbert" | "ann" | "fallback"
    }
"""

import logging

from fastapi import FastAPI
from pydantic import BaseModel

from backend import config
from backend.model_loader import get_classifier, FallbackClassifier, AnnClassifier, DistilBertClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("moderation.api")

app = FastAPI(title="Hate Speech Moderation API")


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    internal_label: str
    category: str | None
    confidence: float
    model_source: str

def _model_source_name(classifier) -> str:
    if isinstance(classifier, DistilBertClassifier):
        return "distilbert"
    if isinstance(classifier, AnnClassifier):
        return "ann"
    if isinstance(classifier, FallbackClassifier):
        return "fallback"
    return "unknown"


@app.get("/health")
def health():
    classifier = get_classifier()
    return {"status": "ok", "model_source": _model_source_name(classifier)}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    classifier = get_classifier()
    label, confidence = classifier.predict(request.text)
    category = config.LABEL_DISPLAY_MAP.get(label, label)

    return PredictResponse(
        internal_label=label,
        category=category,
        confidence=round(confidence, 4),
        model_source=_model_source_name(classifier),
    )
