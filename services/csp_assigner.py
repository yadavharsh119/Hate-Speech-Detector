from sqlalchemy.orm import Session
from constraint import Problem, FunctionConstraint
import models

def assign_moderator(tweet_id: int, severity_category: str, tweet_text: str, db: Session) -> int:
    """
    Assigns a moderator based on CSP constraints:
    - Never assign if active_load >= max_capacity
    - 'Severe' tweets go to 'senior' role moderators
    - Prefer language matches
    
    Returns:
        moderator_id (int) or None if no moderator is available
    """
    moderators = db.query(models.Moderator).all()
    if not moderators:
        return None

    problem = Problem()
    problem.addVariable("moderator", moderators)

    # Constraint (a): active_load < max_capacity
    def capacity_check(mod):
        return mod.active_load < mod.max_capacity

    # Constraint (b): 'Severe' -> 'senior' role
    def seniority_check(mod):
        if severity_category == "Severe":
            return mod.role == "senior"
        return True

    problem.addConstraint(FunctionConstraint(capacity_check), ["moderator"])
    problem.addConstraint(FunctionConstraint(seniority_check), ["moderator"])

    solutions = problem.getSolutions()
    if not solutions:
        return None

    valid_candidates = [sol["moderator"] for sol in solutions]

    # Constraint (c): prefer language matches (soft constraint), then lowest workload
    # We use a simple mock language detection for the tweet text:
    tweet_lang = "es" if "espanol" in tweet_text.lower() or "spanish" in tweet_text.lower() else "en"

    def score_mod(mod):
        mod_langs = [l.strip().lower() for l in (mod.languages or "").split(",") if l.strip()]
        lang_match = 0 if tweet_lang in mod_langs else 1
        ratio = mod.active_load / mod.max_capacity if mod.max_capacity > 0 else 0
        return (lang_match, ratio)

    selected_mod = min(valid_candidates, key=score_mod)
    return selected_mod.id