from sqlalchemy.orm import Session
import models

def assign_moderator(tweet_id: int, severity_category: str, db: Session) -> int:
    """
    Mock CSP routing interface for Member 2 (CSP Specialist).
    
    Member 2: Replace this mock logic with your OR-Tools or python-constraint solver.
    Constraints to implement: Workload limits, Severity prioritization, Language matching.
    
    Returns:
        moderator_id (int) or None if no moderator is available
    """
    
    # Mock logic: Find any available moderator who hasn't reached max capacity,
    # prioritizing those with the lowest active load.
    available_moderator = (
        db.query(models.Moderator)
        .filter(models.Moderator.active_load < models.Moderator.max_capacity)
        .order_by(models.Moderator.active_load.asc())
        .first()
    )
    
    if available_moderator:
        return available_moderator.id
        
    # If no moderators exist or all are full
    return None