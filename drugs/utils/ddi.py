def classify_severity(score: float) -> str:
    if score >= 0.85:
        return "high"
    elif score >= 0.7:
        return "moderate"
    return "low"
