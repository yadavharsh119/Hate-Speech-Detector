import random

def predict_hate_speech(raw_text: str) -> dict:
    """
    Mock AI inference interface for Member 1 (AI Specialist).
    
    Member 1: Replace this mock logic with your trained BiLSTM model and tokenizer.
    
    Expected returns:
    {
        "predicted_category": str,  # "Clean", "Mild", "Moderate Hate", "Severe"
        "confidence_score": float,  # 0.0 to 1.0
        "flagged": bool             # False if Clean, True otherwise
    }
    """
    
    # Mock logic: Generate a random category and score for testing the backend pipeline
    categories = ["Clean", "Mild", "Moderate Hate", "Severe"]
    
    # Simple hardcoded check for demo purposes
    text_lower = raw_text.lower()
    if "hate" in text_lower or "kill" in text_lower:
        category = "Severe"
    elif "stupid" in text_lower or "idiot" in text_lower:
        category = "Mild"
    else:
        # 60% chance it's clean, 40% chance it picks a random issue
        category = "Clean" if random.random() > 0.4 else random.choice(categories[1:])
        
    confidence = round(random.uniform(0.70, 0.99), 2)
    flagged = category != "Clean"
    
    return {
        "predicted_category": category,
        "confidence_score": confidence,
        "flagged": flagged
    }
