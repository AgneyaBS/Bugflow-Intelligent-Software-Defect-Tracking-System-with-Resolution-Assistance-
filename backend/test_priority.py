from app.services.priority_service import calculate_priority
from app.models.issue import Severity


tests = [
    (Severity.CRITICAL, "HIGH"),
    (Severity.MAJOR, "HIGH"),
    (Severity.MINOR, "MEDIUM"),
    (Severity.TRIVIAL, "LOW"),
]


for severity, urgency in tests:

    score, priority = calculate_priority(
        severity,
        urgency
    )

    print(
        f"{severity.value} + {urgency}"
        f" → Score: {score}"
        f" → Priority: {priority.value}"
    )