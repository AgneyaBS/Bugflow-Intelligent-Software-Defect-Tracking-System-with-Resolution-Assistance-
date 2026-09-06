# ============================================================
# BUGFLOW - RESOLUTION ASSISTANCE SERVICE
# ============================================================

from sqlalchemy.orm import Session

from app.models.issue import Issue


def generate_resolution_assistance(
    db: Session,
    issue: Issue
) -> dict:
    """
    Generate structured resolution assistance for an issue.

    This service intentionally does NOT use NLP.
    Resolution guidance is generated using structured
    issue attributes such as category, severity and priority.
    """

    # --------------------------------------------------------
    # Get structured issue information
    # --------------------------------------------------------

    severity = (
        issue.severity.value
        if hasattr(issue.severity, "value")
        else str(issue.severity or "")
    )

    priority = (
        issue.priority.value
        if hasattr(issue.priority, "value")
        else str(issue.priority or "")
    )

    category = ""

    if getattr(issue, "category", None):
        category = (
            issue.category.category_name
            if hasattr(issue.category, "category_name")
            else str(issue.category)
        )

    category = category or "Unknown"


    # --------------------------------------------------------
    # Default guidance
    # --------------------------------------------------------

    analysis = (
        "The issue requires investigation based on its "
        "reported information and current priority."
    )

    resolution = (
        "Reproduce the issue, inspect the affected component, "
        "identify the root cause, apply the appropriate fix, "
        "and verify the result."
    )

    steps = [
        "Reproduce the reported issue.",
        "Inspect the affected component and application logs.",
        "Identify the root cause.",
        "Apply the appropriate correction.",
        "Test the fix and verify the issue is resolved."
    ]

    prevention = (
        "Add appropriate validation, testing, logging, "
        "or monitoring to reduce the chance of recurrence."
    )


    # ========================================================
    # CATEGORY-BASED GUIDANCE
    # ========================================================

    category_lower = category.lower()


    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    if "database" in category_lower:

        analysis = (
            "The issue is categorized as a database problem. "
            "The investigation should focus on database "
            "connectivity, queries, transactions, or configuration."
        )

        resolution = (
            "Verify the database connection and configuration, "
            "inspect database errors and queries, identify the "
            "root cause, and apply the required database or "
            "backend correction."
        )

        steps = [
            "Verify that the database server is running.",
            "Check database host, port, username, password, and database name.",
            "Inspect backend logs for database errors.",
            "Validate the affected SQL query or transaction.",
            "Retest the complete operation after applying the fix."
        ]

        prevention = (
            "Use database health checks, proper exception handling, "
            "query validation, backups, and database monitoring."
        )


    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    elif "authentication" in category_lower:

        analysis = (
            "The issue is categorized as an authentication problem. "
            "The investigation should focus on credentials, JWT "
            "validation, login processing, or authorization."
        )

        resolution = (
            "Inspect the authentication flow, verify credential "
            "validation and JWT handling, check authorization rules, "
            "and correct the failing authentication component."
        )

        steps = [
            "Reproduce the authentication failure.",
            "Verify the submitted credentials.",
            "Inspect JWT creation and token validation.",
            "Verify token expiration and authorization rules.",
            "Retest login and protected API requests."
        ]

        prevention = (
            "Use secure password hashing, token expiration, "
            "consistent authentication validation, and automated "
            "authentication tests."
        )


    # --------------------------------------------------------
    # UI / FRONTEND
    # --------------------------------------------------------

    elif "ui" in category_lower or "frontend" in category_lower:

        analysis = (
            "The issue is categorized as a frontend problem. "
            "The investigation should focus on the affected "
            "HTML, CSS, JavaScript, and browser behavior."
        )

        resolution = (
            "Inspect the affected frontend component, identify "
            "the incorrect UI or browser-side behavior, apply "
            "the required correction, and retest the interface."
        )

        steps = [
            "Reproduce the issue in the browser.",
            "Inspect browser console errors.",
            "Check the affected HTML and CSS.",
            "Inspect JavaScript event handlers and API calls.",
            "Retest the interface after applying the fix."
        ]

        prevention = (
            "Use UI validation, browser testing, JavaScript "
            "error handling, and regression testing."
        )


    # --------------------------------------------------------
    # BACKEND / API
    # --------------------------------------------------------

    elif "backend" in category_lower or "api" in category_lower:

        analysis = (
            "The issue is categorized as a backend or API problem. "
            "The investigation should focus on request processing, "
            "validation, authentication, database operations, "
            "and API responses."
        )

        resolution = (
            "Inspect the affected API endpoint, request data, "
            "validation rules, authentication, database interaction, "
            "and response handling to identify and correct the failure."
        )

        steps = [
            "Reproduce the API request.",
            "Check the request payload and authentication token.",
            "Inspect backend logs and endpoint logic.",
            "Verify validation and database operations.",
            "Retest the API and confirm the expected response."
        ]

        prevention = (
            "Add API validation, exception handling, logging, "
            "automated endpoint tests, and monitoring."
        )


    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    elif "performance" in category_lower:

        analysis = (
            "The issue is categorized as a performance problem. "
            "The investigation should focus on response time, "
            "database queries, resource usage, and expensive operations."
        )

        resolution = (
            "Measure the slow operation, identify the performance "
            "bottleneck, optimize the affected component, and "
            "measure the result again."
        )

        steps = [
            "Reproduce the performance problem.",
            "Measure API and database response times.",
            "Inspect slow queries and backend processing.",
            "Identify expensive or unnecessary operations.",
            "Apply the optimization and measure performance again."
        ]

        prevention = (
            "Use performance monitoring, query optimization, "
            "appropriate caching, and regular load testing."
        )


    # ========================================================
    # SEVERITY / PRIORITY INFORMATION
    # ========================================================

    priority_note = (
        f"The issue has severity '{severity}' and "
        f"priority '{priority}'."
    )


    analysis = (
        f"{analysis} {priority_note}"
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "issue_id": issue.id,
        "issue_key": getattr(issue, "issue_key", None),
        "category": category,
        "severity": severity,
        "priority": priority,
        "analysis": analysis,
        "resolution": resolution,
        "steps": steps,
        "prevention": prevention
    }