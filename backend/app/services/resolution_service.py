# ============================================================
# BUGFLOW - RESOLUTION ASSISTANCE SERVICE
# ============================================================

from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.bug_category import BugCategory


# ============================================================
# SERVICE LOAD DEBUG
# ============================================================

print("================================================")
print("BUGFLOW RESOLUTION SERVICE LOADED")
print("FILE:", __file__)
print("================================================")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _get_enum_value(value) -> str:
    """
    Safely get the value of an Enum or normal string.
    """

    if value is None:
        return ""

    if hasattr(value, "value"):
        return str(value.value)

    return str(value)


def _contains_any(text: str, keywords: list[str]) -> bool:
    """
    Check whether any keyword exists in the supplied text.

    This is deterministic keyword matching.
    It does NOT use NLP or machine learning.
    """

    text = text.lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


# ============================================================
# MAIN RESOLUTION ASSISTANCE FUNCTION
# ============================================================

def generate_resolution_assistance(
    db: Session,
    issue: Issue
) -> dict:
    """
    Generate issue-specific resolution assistance.

    The service does NOT use NLP or machine learning.

    Guidance is generated using:
        - Issue category
        - Issue severity
        - Issue priority
        - Issue title
        - Issue description
        - Issue type
    """

    # ========================================================
    # 1. BASIC ISSUE INFORMATION
    # ========================================================

    issue_id = issue.id

    issue_key = getattr(
        issue,
        "issue_key",
        None
    )

    title = str(
        getattr(issue, "title", "") or ""
    )

    description = str(
        getattr(issue, "description", "") or ""
    )

    # ========================================================
    # 2. SEVERITY / PRIORITY / ISSUE TYPE
    # ========================================================

    severity = _get_enum_value(
        getattr(issue, "severity", None)
    )

    priority = _get_enum_value(
        getattr(issue, "priority", None)
    )

    issue_type = _get_enum_value(
        getattr(issue, "issue_type", None)
    )
# ========================================================
# 3. CATEGORY
# ========================================================

    category = "Unknown"

    category_id = getattr(issue, "category_id", None)

    print("CATEGORY DEBUG")
    print("Category ID from Issue :", category_id)

    if category_id is not None:

        issue_category = (
        db.query(BugCategory)
        .filter(
            BugCategory.category_id == int(category_id)
        )
        .first()
    )

    print("Category DB Result     :", issue_category)

    if issue_category:
        print(
            "Category Name from DB  :",
            issue_category.category_name
        )

        category = issue_category.category_name

    category_lower = category.lower()

    print("Final Category         :", category)
    print("Final Category Lower   :", category_lower)
# ========================================================
# 4. COMBINED ISSUE TEXT
# ========================================================

    issue_text = (
        f"{title} {description}"
    ).lower()

    # ========================================================
    # DEBUG INFORMATION
    # ========================================================

    print("\n")
    print("================================================")
    print("       BUGFLOW RESOLUTION DEBUG")
    print("================================================")
    print("Issue ID       :", issue_id)
    print("Issue Key      :", issue_key)
    print("Title          :", title)
    print("Description    :", description)
    print("Category ID    :", getattr(issue, "category_id", None))
    print("Category       :", category)
    print("Category Lower :", category_lower)
    print("Severity       :", severity)
    print("Priority       :", priority)
    print("Issue Type     :", issue_type)
    print("Issue Text     :", issue_text)
    print("================================================")

    # ========================================================
    # 5. DEFAULT GUIDANCE
    # ========================================================

    analysis = (
        "The issue should be investigated using the reported "
        "information, affected component, severity, and priority."
    )

    resolution = (
        "Reproduce the reported behavior, inspect the affected "
        "component, identify the cause, apply the required "
        "correction, and verify the result."
    )

    steps = [
        "Review the issue title and description.",
        "Reproduce the reported behavior.",
        "Inspect the affected application component and logs.",
        "Identify the likely cause and apply the correction.",
        "Retest the issue and verify that the expected behavior is restored."
    ]

    prevention = (
        "Add appropriate validation, testing, logging, "
        "and monitoring to reduce the chance of recurrence."
    )

    selected_rule = "DEFAULT"

    # ========================================================
    # 6. DATABASE / CONNECTION ISSUES
    # ========================================================

    database_keywords = [
        "database",
        "db",
        "postgres",
        "postgresql",
        "sql",
        "query",
        "connection",
        "connect",
        "db connection",
        "database connection",
        "connection refused",
        "connection failed",
        "connection failure",
        "connect failed",
        "unable to connect",
        "cannot connect",
        "could not connect",
        "server connection",
        "server unavailable",
        "database unavailable",
        "database down",
        "database server",
        "foreign key",
        "constraint",
        "transaction",
        "table",
        "column"
    ]

    if (
        "database" in category_lower
        or "db" in category_lower
        or _contains_any(issue_text, database_keywords)
    ):

        # ----------------------------------------------------
        # Database connection
        # ----------------------------------------------------

        connection_keywords = [
            "connection",
            "connect",
            "connection refused",
            "connection failed",
            "connection failure",
            "connect failed",
            "unable to connect",
            "cannot connect",
            "could not connect",
            "server connection",
            "server unavailable",
            "database unavailable",
            "database down",
            "database server",
            "host unreachable",
            "connection timeout",
            "database timeout"
        ]

        if _contains_any(
            issue_text,
            connection_keywords
        ):

            selected_rule = "DATABASE / CONNECTION"

            print(">>> DATABASE / CONNECTION RULE SELECTED")

            analysis = (
                "The issue appears to involve server or database "
                "connectivity. The investigation should focus on "
                "the database/server availability, host and port "
                "configuration, credentials, network access, "
                "connection settings, and connection pooling."
            )

            resolution = (
                "Verify that the required server or database is "
                "available and that the application is using the "
                "correct host, port, credentials, and database name. "
                "Inspect the connection error and correct the "
                "configuration, network access, or server availability problem."
            )

            steps = [
                "Reproduce the connection failure.",
                "Verify that the PostgreSQL/database or required server is running.",
                "Check the configured host and port.",
                "Verify the database name, username, and credentials.",
                "Inspect backend logs for the exact connection error.",
                "Check network access and firewall settings if required.",
                "Retest the affected operation after correcting the configuration."
            ]

            prevention = (
                "Use server and database health checks, connection "
                "monitoring, connection-pool configuration, "
                "configuration validation, and automated connectivity tests."
            )

        # ----------------------------------------------------
        # SQL / query problems
        # ----------------------------------------------------

        elif _contains_any(
            issue_text,
            [
                "query",
                "sql",
                "select",
                "insert",
                "update",
                "delete"
            ]
        ):

            selected_rule = "DATABASE / SQL"

            print(">>> DATABASE / SQL RULE SELECTED")

            analysis = (
                "The issue appears to involve a database query or "
                "database operation. The investigation should focus "
                "on the SQL statement, parameters, schema, and "
                "database response."
            )

            resolution = (
                "Inspect the failing SQL operation and its parameters, "
                "verify that the referenced tables and columns exist, "
                "correct the query or database interaction, and "
                "retest the operation."
            )

            steps = [
                "Reproduce the database operation.",
                "Capture the failing SQL query and parameters.",
                "Verify the affected tables, columns, and constraints.",
                "Correct the query or backend database operation.",
                "Retest the complete application workflow."
            ]

            prevention = (
                "Use query validation, database integration tests, "
                "schema migration checks, and SQL error monitoring."
            )

        # ----------------------------------------------------
        # General database problem
        # ----------------------------------------------------

        else:

            selected_rule = "DATABASE"

            print(">>> DATABASE RULE SELECTED")

            analysis = (
                "The issue is related to database functionality. "
                "The investigation should focus on database access, "
                "queries, transactions, schema configuration, and "
                "backend database handling."
            )

            resolution = (
                "Inspect the database operation associated with the "
                "issue, verify the schema and configuration, identify "
                "the failing database interaction, apply the required "
                "correction, and retest the operation."
            )

            steps = [
                "Reproduce the database-related issue.",
                "Inspect backend logs and database errors.",
                "Check the affected database operation and schema.",
                "Apply the required database or backend correction.",
                "Retest the affected workflow."
            ]

            prevention = (
                "Use database integration tests, health checks, "
                "schema validation, logging, and monitoring."
            )

    # ========================================================
    # 7. AUTHENTICATION / LOGIN ISSUES
    # ========================================================

    elif (
        "authentication" in category_lower
        or "authorization" in category_lower
        or "login" in category_lower
        or _contains_any(
            issue_text,
            [
                "login",
                "logout",
                "password",
                "jwt",
                "token",
                "authentication",
                "authorization",
                "unauthorized",
                "forbidden",
                "403",
                "401",
                "sign in",
                "signin"
            ]
        )
    ):

        # ----------------------------------------------------
        # Login failure
        # ----------------------------------------------------

        if _contains_any(
            issue_text,
            [
                "login",
                "sign in",
                "signin"
            ]
        ):

            selected_rule = "AUTHENTICATION / LOGIN"

            print(">>> AUTHENTICATION / LOGIN RULE SELECTED")

            analysis = (
                "The issue appears to affect the login process. "
                "The investigation should focus on credential "
                "validation, authentication requests, password "
                "verification, and the returned authentication response."
            )

            resolution = (
                "Inspect the login request and authentication flow. "
                "Verify that the submitted credentials reach the backend "
                "correctly, confirm password verification, inspect the "
                "authentication response, and correct the failing step."
            )

            steps = [
                "Reproduce the login failure.",
                "Inspect the browser request and login payload.",
                "Verify backend credential validation.",
                "Check password hashing and verification.",
                "Inspect the authentication response.",
                "Retest successful login and protected-page access."
            ]

            prevention = (
                "Add automated login tests, authentication error logging, "
                "input validation, and regression tests for the login flow."
            )

        # ----------------------------------------------------
        # JWT / token
        # ----------------------------------------------------

        elif _contains_any(
            issue_text,
            [
                "jwt",
                "token",
                "expired token",
                "invalid token"
            ]
        ):

            selected_rule = "AUTHENTICATION / JWT"

            print(">>> AUTHENTICATION / JWT RULE SELECTED")

            analysis = (
                "The issue appears to involve authentication tokens. "
                "The investigation should focus on token generation, "
                "storage, expiration, decoding, and validation."
            )

            resolution = (
                "Inspect token generation and validation, verify the "
                "token payload and expiration time, confirm that the "
                "client sends the correct Authorization header, and "
                "correct the failing authentication step."
            )

            steps = [
                "Reproduce the authentication failure.",
                "Inspect the Authorization header sent by the client.",
                "Verify JWT creation and payload information.",
                "Check token expiration and signature validation.",
                "Retest the protected API request."
            ]

            prevention = (
                "Use consistent JWT validation, token expiration, "
                "secure token handling, and automated protected-endpoint tests."
            )

        # ----------------------------------------------------
        # General authentication / authorization
        # ----------------------------------------------------

        else:

            selected_rule = "AUTHENTICATION / AUTHORIZATION"

            print(">>> AUTHENTICATION / AUTHORIZATION RULE SELECTED")

            analysis = (
                "The issue appears to involve authentication or "
                "authorization. The investigation should focus on "
                "identity verification, access rules, credentials, "
                "and protected API requests."
            )

            resolution = (
                "Trace the authentication and authorization flow, "
                "verify the current user's identity and permissions, "
                "identify the failing access check, and correct the "
                "authentication configuration or authorization rule."
            )

            steps = [
                "Reproduce the authentication or authorization failure.",
                "Inspect the authenticated user information.",
                "Check the required permissions and access rules.",
                "Inspect the protected API response.",
                "Retest the operation with the correct permissions."
            ]

            prevention = (
                "Use centralized authentication, consistent RBAC rules, "
                "automated authorization tests, and security logging."
            )

    # ========================================================
    # 8. FRONTEND / UI ISSUES
    # ========================================================

    elif (
        "ui" in category_lower
        or "frontend" in category_lower
        or "front end" in category_lower
        or _contains_any(
            issue_text,
            [
                "button",
                "click",
                "onclick",
                "page",
                "screen",
                "css",
                "html",
                "javascript",
                "layout",
                "design",
                "display",
                "responsive",
                "mobile",
                "alignment",
                "dropdown",
                "form",
                "modal",
                "navbar",
                "sidebar"
            ]
        )
    ):

        # ----------------------------------------------------
        # Button / interaction
        # ----------------------------------------------------

        if _contains_any(
            issue_text,
            [
                "button",
                "click",
                "not working",
                "onclick"
            ]
        ):

            selected_rule = "FRONTEND / BUTTON"

            print(">>> FRONTEND / BUTTON RULE SELECTED")

            analysis = (
                "The issue appears to involve a frontend interaction. "
                "The investigation should focus on the affected button, "
                "event handler, JavaScript logic, and API request."
            )

            resolution = (
                "Inspect the affected button and its event handler, "
                "verify that the JavaScript function is executed, "
                "check any API request triggered by the action, "
                "and correct the failing frontend logic."
            )

            steps = [
                "Reproduce the button interaction.",
                "Inspect browser console errors.",
                "Verify the button event handler.",
                "Check JavaScript execution and API requests.",
                "Inspect the network request and response.",
                "Retest the button after applying the correction."
            ]

            prevention = (
                "Use frontend event testing, browser console monitoring, "
                "JavaScript error handling, and UI regression tests."
            )

        # ----------------------------------------------------
        # Mobile / responsive
        # ----------------------------------------------------

        elif _contains_any(
            issue_text,
            [
                "mobile",
                "responsive",
                "phone",
                "screen size"
            ]
        ):

            selected_rule = "FRONTEND / RESPONSIVE"

            print(">>> FRONTEND / RESPONSIVE RULE SELECTED")

            analysis = (
                "The issue appears to involve responsive frontend "
                "behavior. The investigation should focus on layout "
                "rules, viewport handling, CSS breakpoints, and "
                "mobile-specific rendering."
            )

            resolution = (
                "Inspect the responsive layout and CSS breakpoints, "
                "identify the element that behaves incorrectly on "
                "smaller screens, adjust the layout rules, and verify "
                "the page across multiple viewport sizes."
            )

            steps = [
                "Reproduce the issue using a mobile viewport.",
                "Inspect the affected HTML elements.",
                "Check CSS media queries and responsive rules.",
                "Correct the layout or sizing behavior.",
                "Test the page on mobile, tablet, and desktop sizes."
            ]

            prevention = (
                "Use responsive design testing, multiple viewport tests, "
                "and UI regression testing."
            )

        # ----------------------------------------------------
        # General frontend issue
        # ----------------------------------------------------

        else:

            selected_rule = "FRONTEND / UI"

            print(">>> FRONTEND / UI RULE SELECTED")

            analysis = (
                "The issue appears to affect the frontend interface. "
                "The investigation should focus on HTML, CSS, JavaScript, "
                "browser behavior, and the affected UI component."
            )

            resolution = (
                "Inspect the affected frontend component, identify the "
                "incorrect browser-side behavior or visual rule, apply "
                "the required correction, and verify the interface."
            )

            steps = [
                "Reproduce the issue in the browser.",
                "Inspect browser console errors.",
                "Inspect the affected HTML and CSS.",
                "Check related JavaScript and API calls.",
                "Retest the interface after the correction."
            ]

            prevention = (
                "Use UI validation, browser testing, JavaScript error "
                "handling, and frontend regression testing."
            )

    # ========================================================
    # 9. BACKEND / API ISSUES
    # ========================================================

    elif (
        "backend" in category_lower
        or "api" in category_lower
        or _contains_any(
            issue_text,
            [
                "api",
                "endpoint",
                "server error",
                "internal server",
                "500",
                "404",
                "request",
                "response",
                "fastapi"
            ]
        )
    ):

        # ----------------------------------------------------
        # 500 / server error
        # ----------------------------------------------------

        if _contains_any(
            issue_text,
            [
                "500",
                "internal server",
                "server error"
            ]
        ):

            selected_rule = "BACKEND / SERVER ERROR"

            print(">>> BACKEND / SERVER ERROR RULE SELECTED")

            analysis = (
                "The issue appears to involve a backend server error. "
                "The investigation should focus on the failing endpoint, "
                "request processing, exceptions, database operations, "
                "and server logs."
            )

            resolution = (
                "Reproduce the failing API request, inspect the backend "
                "logs and stack trace, identify the failing operation, "
                "correct the backend logic or data handling, and retest "
                "the endpoint."
            )

            steps = [
                "Reproduce the API request.",
                "Inspect the FastAPI/server logs and traceback.",
                "Identify the function or operation causing the error.",
                "Correct the backend logic or data handling.",
                "Retest the endpoint with valid and invalid inputs."
            ]

            prevention = (
                "Use exception handling, API tests, structured logging, "
                "input validation, and backend monitoring."
            )

        # ----------------------------------------------------
        # 404
        # ----------------------------------------------------

        elif _contains_any(
            issue_text,
            [
                "404",
                "not found",
                "missing endpoint"
            ]
        ):

            selected_rule = "BACKEND / 404"

            print(">>> BACKEND / 404 RULE SELECTED")

            analysis = (
                "The issue appears to involve a missing API resource "
                "or endpoint. The investigation should focus on the "
                "requested URL, router registration, resource ID, "
                "and endpoint configuration."
            )

            resolution = (
                "Verify the requested API path and resource identifier, "
                "check that the corresponding FastAPI router is registered, "
                "and correct the URL, route, or missing resource."
            )

            steps = [
                "Reproduce the 404 request.",
                "Verify the requested URL and HTTP method.",
                "Check the FastAPI router and endpoint registration.",
                "Verify the requested resource ID.",
                "Retest the endpoint."
            ]

            prevention = (
                "Use API integration tests, route documentation, "
                "endpoint validation, and automated regression tests."
            )

        # ----------------------------------------------------
        # General backend/API
        # ----------------------------------------------------

        else:

            selected_rule = "BACKEND / API"

            print(">>> BACKEND / API RULE SELECTED")

            analysis = (
                "The issue appears to involve backend or API processing. "
                "The investigation should focus on the request, validation, "
                "authentication, database interaction, endpoint logic, "
                "and response."
            )

            resolution = (
                "Inspect the affected API endpoint and request data, "
                "trace the request through backend processing, identify "
                "the failing operation, apply the correction, and verify "
                "the expected response."
            )

            steps = [
                "Reproduce the API request.",
                "Check the request payload and authentication.",
                "Inspect endpoint logic and backend logs.",
                "Verify validation and database operations.",
                "Retest the API and confirm the expected response."
            ]

            prevention = (
                "Add API validation, exception handling, logging, "
                "automated endpoint tests, and monitoring."
            )

    # ========================================================
    # 10. PERFORMANCE ISSUES
    # ========================================================

    elif (
        "performance" in category_lower
        or _contains_any(
            issue_text,
            [
                "slow",
                "latency",
                "response time",
                "performance",
                "timeout",
                "loading slowly"
            ]
        )
    ):

        selected_rule = "PERFORMANCE"

        print(">>> PERFORMANCE RULE SELECTED")

        analysis = (
            "The issue appears to involve application performance. "
            "The investigation should focus on response time, database "
            "queries, backend processing, resource usage, and expensive "
            "operations."
        )

        resolution = (
            "Measure the affected operation, identify the performance "
            "bottleneck, optimize the responsible component, and "
            "measure the result again to verify the improvement."
        )

        steps = [
            "Reproduce the performance problem.",
            "Measure the API and page response time.",
            "Inspect database queries and backend processing.",
            "Identify expensive or unnecessary operations.",
            "Apply the optimization and measure performance again."
        ]

        prevention = (
            "Use performance monitoring, query optimization, appropriate "
            "caching, profiling, and regular load testing."
        )

    # ========================================================
    # 11. BUG / FUNCTIONAL ISSUE
    # ========================================================

    else:

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if _contains_any(
            issue_text,
            [
                "validation",
                "invalid input",
                "error message",
                "form"
            ]
        ):

            selected_rule = "FUNCTIONAL / VALIDATION"

            print(">>> FUNCTIONAL / VALIDATION RULE SELECTED")

            analysis = (
                "The issue appears to involve input or data validation. "
                "The investigation should focus on the input values, "
                "validation rules, error handling, and the affected "
                "application workflow."
            )

            resolution = (
                "Reproduce the validation failure, inspect the input "
                "and validation rules, identify the incorrect validation "
                "behavior, update the validation logic, and retest valid "
                "and invalid inputs."
            )

            steps = [
                "Reproduce the validation problem.",
                "Identify the input that causes the failure.",
                "Inspect frontend and backend validation rules.",
                "Correct the validation or error-handling logic.",
                "Test both valid and invalid input cases."
            ]

            prevention = (
                "Use centralized validation, boundary testing, "
                "negative test cases, and automated validation tests."
            )

        # ----------------------------------------------------
        # Generic functional bug
        # ----------------------------------------------------

        else:

            selected_rule = "GENERIC FUNCTIONAL"

            print(">>> GENERIC FUNCTIONAL RULE SELECTED")

            analysis = (
                f"The issue '{title or issue_key or issue_id}' requires "
                "functional investigation based on the reported behavior. "
                "The title and description should be used to reproduce "
                "the problem and identify the affected component."
            )

            resolution = (
                "Reproduce the exact behavior described in the issue, "
                "compare the actual result with the expected result, "
                "trace the affected application flow, identify the "
                "failing component, apply the correction, and verify "
                "the complete workflow."
            )

            steps = [
                "Review the issue title and description carefully.",
                "Reproduce the exact reported behavior.",
                "Compare the actual result with the expected result.",
                "Trace the affected application component and identify the cause.",
                "Apply the correction and retest the complete workflow."
            ]

            prevention = (
                "Add a regression test for the reported scenario and "
                "include the affected workflow in future testing."
            )

    # ========================================================
    # 12. FINAL DEBUG INFORMATION
    # ========================================================

    print("------------------------------------------------")
    print("SELECTED RESOLUTION RULE:", selected_rule)
    print("------------------------------------------------")

    # ========================================================
    # 13. SEVERITY AND PRIORITY INFORMATION
    # ========================================================

    priority_note = (
        f"The issue has severity '{severity or 'Not specified'}' "
        f"and priority '{priority or 'Not specified'}'."
    )

    analysis = (
        f"{analysis} {priority_note}"
    )

    # ========================================================
    # 14. RETURN STRUCTURED RESULT
    # ========================================================

    return {
        "issue_id": issue_id,
        "issue_key": issue_key,
        "category": category,
        "severity": severity,
        "priority": priority,
        "analysis": analysis,
        "resolution": resolution,
        "steps": steps,
        "prevention": prevention
    }