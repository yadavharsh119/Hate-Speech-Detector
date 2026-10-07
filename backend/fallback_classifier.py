"""
Deterministic, rule-based fallback classifier.

Used ONLY when the real trained model's artifact folder is missing (e.g.
before the teammate who trained it has shared the weights). This is
intentionally simple and fully deterministic — no randomness — so it gives
consistent, explainable output and clearly-worse accuracy than the real
model, making it obvious in testing/demo that it's a stand-in, not the
real thing.

This is NOT meant to be a serious classifier. It exists so the rest of the
pipeline (API, frontend, DB, CSP assignment) can be built and tested before
the real model artifacts arrive, per the "drop-in" design goal.
"""

import re

# Small, deliberately coarse keyword lists. Real classification logic lives
# in the trained models — this is just enough to produce varied, sane-looking
# output for integration testing.
_THREAT_PATTERNS = [
    r"\bkill you\b", r"\bi will kill\b", r"\bi'll kill\b",
    r"\bgonna kill\b", r"\bshoot you\b", r"\bburn your house\b",
    r"\bi will hurt you\b", r"\bi'll hurt you\b",
]

_HATE_PATTERNS = [
    r"\bi hate (all|every)\b",
    r"\bsubhuman\b", r"\bgo back to your country\b",
    r"\bshould not exist\b",
]

_OFFENSIVE_PATTERNS = [
    r"\bidiot\b", r"\bstupid\b", r"\bshut up\b", r"\bloser\b",
    r"\bugly\b", r"\bpathetic\b",
]


def _matches_any(patterns, text_lower):
    return any(re.search(p, text_lower) for p in patterns)


def classify(text: str):
    """
    Returns (label, confidence) using the internal training label names
    (hate / offensive / safe / threat), same contract as the real models,
    so callers never need to know which backend is active.

    Confidence is a fixed, low placeholder value (0.50) regardless of match,
    to make it visually obvious in logs/UI that this is the fallback path
    and not a real model's calibrated confidence score.
    """
    if not text or not text.strip():
        return "safe", 0.50

    text_lower = text.lower()

    if _matches_any(_THREAT_PATTERNS, text_lower):
        return "threat", 0.50
    if _matches_any(_HATE_PATTERNS, text_lower):
        return "hate", 0.50
    if _matches_any(_OFFENSIVE_PATTERNS, text_lower):
        return "offensive", 0.50

    return "safe", 0.50
