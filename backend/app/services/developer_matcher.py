import re
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.issue import Issue, IssueStatus


# ============================================================
# SMART DEVELOPER MATCHER
# ============================================================

# Keywords related to common development areas
SKILL_KEYWORDS = {
    "database": [
        "database",
        "postgresql",
        "postgres",
        "sql",
        "mysql",
        "oracle",
        "db",
        "query",
        "connection",
        "timeout",
    ],

    "backend": [
        "backend",
        "server",
        "api",
        "endpoint",
        "fastapi",
        "flask",
        "django",
        "rest",
    ],

    "python": [
        "python",
        "fastapi",
        "flask",
        "django",
        "script",
    ],

    "frontend": [
        "frontend",
        "html",
        "css",
        "javascript",
        "js",
        "react",
        "ui",
        "button",
        "page",
        "design",
    ],

    "authentication": [
        "login",
        "logout",
        "authentication",
        "authorization",
        "jwt",
        "token",
        "password",
        "signin",
        "signup",
    ],
}


# ============================================================
# EXTRACT KEYWORDS FROM BUG
# ============================================================

def extract_bug_keywords(title: str, description: str) -> List[str]:
    """
    Extract relevant technical keywords from issue title
    and description.
    """

    text = f"{title} {description}".lower()

    detected_keywords = []

    for category, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r"\b" + re.escape(keyword) + r"\b", text):
                detected_keywords.append(keyword)

    return list(set(detected_keywords))


# ============================================================
# FIND SKILL MATCH
# ============================================================

def calculate_skill_match(
    bug_keywords: List[str],
    developer_skills: str | None
) -> tuple[float, List[str]]:
    """
    Calculate how well a developer's skills match
    the detected bug keywords.
    """

    if not developer_skills:
        return 0.0, []

    skills = [
        skill.strip().lower()
        for skill in developer_skills.split(",")
        if skill.strip()
    ]

    matched_skills = []

    for keyword in bug_keywords:
        for skill in skills:
            if keyword == skill or keyword in skill or skill in keyword:
                matched_skills.append(keyword)
                break

    if not bug_keywords:
        return 0.0, []

    match_percentage = (
        len(set(matched_skills)) / len(set(bug_keywords))
    ) * 100

    return round(match_percentage, 2), list(set(matched_skills))


# ============================================================
# CALCULATE CURRENT WORKLOAD
# ============================================================

def get_open_bug_count(
    db: Session,
    developer_id: int
) -> int:
    """
    Count currently open issues assigned to a developer.
    """

    closed_statuses = [
        IssueStatus.RESOLVED,
        IssueStatus.CLOSED,
    ]

    count = (
        db.query(Issue)
        .filter(
            Issue.assignee_id == developer_id,
            ~Issue.status.in_(closed_statuses)
        )
        .count()
    )

    return count


# ============================================================
# GENERATE RECOMMENDATIONS
# ============================================================

def recommend_developers(
    db: Session,
    title: str,
    description: str
) -> List[Dict]:

    bug_keywords = extract_bug_keywords(
        title,
        description
    )

    developers = (
        db.query(User)
        .filter(
            User.role == "DEVELOPER",
            User.is_active == True
        )
        .all()
    )

    recommendations = []

    for developer in developers:

        skill_percentage, matched_skills = calculate_skill_match(
            bug_keywords,
            developer.core_skills
        )

        workload = get_open_bug_count(
            db,
            developer.id
        )

        # Workload bonus:
        # Developers with fewer open bugs get a small advantage.
        workload_score = max(
            0,
            20 - (workload * 5)
        )

        # Final score:
        # 80% skill match + 20% workload availability
        final_score = (
            (skill_percentage * 0.8)
            + (workload_score * 0.2)
        )

        if matched_skills:
            reason = (
                f"Matched skills: "
                f"{', '.join(matched_skills)}. "
                f"Currently handling {workload} open issue(s)."
            )
        else:
            reason = (
                f"No direct skill match found. "
                f"Currently handling {workload} open issue(s)."
            )

        recommendations.append({
            "developer_id": developer.id,
            "developer_name": developer.full_name,
            "username": developer.username,
            "match_percentage": round(final_score, 2),
            "matched_skills": matched_skills,
            "open_bugs": workload,
            "reason": reason,
        })

    # Highest match first
    recommendations.sort(
        key=lambda x: x["match_percentage"],
        reverse=True
    )

    # Return top 3 developers
    return recommendations[:3]