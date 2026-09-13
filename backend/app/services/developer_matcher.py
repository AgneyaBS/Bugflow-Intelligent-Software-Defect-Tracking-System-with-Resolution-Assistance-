import re
from typing import List, Dict

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.issue import Issue, IssueStatus


# ============================================================
# ISSUE KEYWORDS → REQUIRED SKILL CATEGORIES
# ============================================================

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
        "screen",
        "display",
        "form",
        "dropdown",
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
        "session",
        "credential",
    ],
}


# ============================================================
# DEVELOPER SKILL ALIASES
# ============================================================

SKILL_ALIASES = {

    "database": {
        "database",
        "db",
        "postgres",
        "postgresql",
        "sql",
        "mysql",
        "oracle",
        "database management",
        "dbms",
    },

    "backend": {
        "backend",
        "server",
        "api",
        "rest",
        "rest api",
        "fastapi",
        "flask",
        "django",
    },

    "python": {
        "python",
        "python programming",
        "fastapi",
        "flask",
        "django",
    },

    "frontend": {
        "frontend",
        "front end",
        "html",
        "css",
        "javascript",
        "js",
        "react",
        "ui",
        "user interface",
        "web development",
    },

    "authentication": {
        "authentication",
        "authorization",
        "jwt",
        "security",
        "login",
        "password",
        "oauth",
        "identity",
    },
}


# ============================================================
# EXTRACT ISSUE KEYWORDS
# ============================================================

def extract_bug_keywords(
    title: str,
    description: str
) -> List[str]:

    text = f"{title} {description}".lower()

    detected_keywords = []

    for category, keywords in SKILL_KEYWORDS.items():

        for keyword in keywords:

            if re.search(
                r"\b" + re.escape(keyword) + r"\b",
                text
            ):
                detected_keywords.append(keyword)

    return list(set(detected_keywords))


# ============================================================
# DETECT REQUIRED CATEGORIES
# ============================================================

def detect_required_categories(
    bug_keywords: List[str]
) -> List[str]:

    required_categories = []

    for category, keywords in SKILL_KEYWORDS.items():

        for keyword in bug_keywords:

            if keyword in keywords:

                required_categories.append(category)

                break

    return list(set(required_categories))


# ============================================================
# CALCULATE SKILL MATCH
# ============================================================

def calculate_skill_match(
    bug_keywords: List[str],
    developer_skills: str | None
) -> tuple[float, List[str]]:

    if not developer_skills:

        return 0.0, []


    # Convert developer skills into clean list

    skills = [
        skill.strip().lower()
        for skill in developer_skills.split(",")
        if skill.strip()
    ]


    required_categories = detect_required_categories(
        bug_keywords
    )


    matched_categories = []


    # --------------------------------------------------------
    # Compare developer skills with required categories
    # --------------------------------------------------------

    for category in required_categories:

        aliases = SKILL_ALIASES.get(
            category,
            set()
        )

        for skill in skills:

            # Direct skill match

            if skill in aliases:

                matched_categories.append(category)

                break


            # Partial match

            for alias in aliases:

                if (
                    alias in skill
                    or skill in alias
                ):

                    matched_categories.append(
                        category
                    )

                    break

            if category in matched_categories:

                break


    matched_categories = list(
        set(matched_categories)
    )


    if not required_categories:

        return 0.0, []


    match_percentage = (
        len(matched_categories)
        /
        len(required_categories)
    ) * 100


    return (
        round(match_percentage, 2),
        matched_categories
    )


# ============================================================
# GET OPEN ISSUE COUNT
# ============================================================

def get_open_bug_count(
    db: Session,
    developer_id: int
) -> int:

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
# WORKLOAD SCORE
# ============================================================

def calculate_workload_score(
    workload: int
) -> float:

    # Maximum workload points = 20

    score = max(
        0,
        20 - (workload * 5)
    )

    return score


# ============================================================
# MAIN DEVELOPER RECOMMENDER
# ============================================================

def recommend_developers(
    db: Session,
    title: str,
    description: str
) -> List[Dict]:

    # --------------------------------------------------------
    # Extract issue keywords
    # --------------------------------------------------------

    bug_keywords = extract_bug_keywords(
        title,
        description
    )


    # --------------------------------------------------------
    # Find active developers
    # --------------------------------------------------------

    developers = (
        db.query(User)
        .filter(
            User.role == "DEVELOPER",
            User.is_active == True
        )
        .all()
    )


    recommendations = []


    # --------------------------------------------------------
    # Calculate score for every developer
    # --------------------------------------------------------

    for developer in developers:

        skill_percentage, matched_skills = (
            calculate_skill_match(
                bug_keywords,
                developer.core_skills
            )
        )


        workload = get_open_bug_count(
            db,
            developer.id
        )


        workload_score = calculate_workload_score(
            workload
        )


        # ----------------------------------------------------
        # Final score
        #
        # Skill = 80%
        # Workload = 20%
        # ----------------------------------------------------

        final_score = (
            (skill_percentage * 0.80)
            +
            (workload_score * 0.20)
        )


        # ----------------------------------------------------
        # Generate recommendation reason
        # ----------------------------------------------------

        if matched_skills:

            reason = (
                f"Matched skill areas: "
                f"{', '.join(matched_skills)}. "
                f"Currently handling "
                f"{workload} open issue(s)."
            )

        else:

            reason = (
                "No direct skill match found. "
                f"Currently handling "
                f"{workload} open issue(s)."
            )


        recommendations.append({

            "developer_id":
                developer.id,

            "developer_name":
                developer.full_name,

            "username":
                developer.username,

            "match_percentage":
                round(final_score, 2),

            "matched_skills":
                matched_skills,

            "open_bugs":
                workload,

            "reason":
                reason,

        })


    # --------------------------------------------------------
    # Highest score first
    # --------------------------------------------------------

    recommendations.sort(
        key=lambda x:
            x["match_percentage"],
        reverse=True
    )


    # Return top 3

    return recommendations[:3]