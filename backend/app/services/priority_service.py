from app.models.issue import Severity, Priority


# ============================================================
# SEVERITY WEIGHTS
# ============================================================

SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 4,
    Severity.MAJOR: 3,
    Severity.MINOR: 2,
    Severity.TRIVIAL: 1,
}


# ============================================================
# CATEGORY URGENCY WEIGHTS
# ============================================================

URGENCY_WEIGHTS = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


# ============================================================
# CALCULATE PRIORITY
# ============================================================

def calculate_priority(
    severity: Severity,
    urgency: str
) -> tuple[float, Priority]:

    # Get severity weight
    severity_weight = SEVERITY_WEIGHTS.get(
        severity,
        1
    )

    # Normalize urgency
    urgency = urgency.upper()

    # Get category urgency weight
    urgency_weight = URGENCY_WEIGHTS.get(
        urgency,
        1
    )

    # Calculate priority score
    priority_score = float(
        severity_weight * urgency_weight
    )

    # Determine final priority
    if priority_score >= 10:
        priority = Priority.URGENT

    elif priority_score >= 7:
        priority = Priority.HIGH

    elif priority_score >= 4:
        priority = Priority.MEDIUM

    else:
        priority = Priority.LOW

    return priority_score, priority