
# ============================================================
# BUGFLOW - RESOLUTION ASSISTANCE SERVICE
# Rule-based issue-specific resolution assistance
# ============================================================

from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.bug_category import BugCategory


print("================================================")
print("BUGFLOW RESOLUTION SERVICE LOADED")
print("FILE:", __file__)
print("================================================")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _get_enum_value(value) -> str:
    """Convert an Enum or normal value into a string."""

    if value is None:
        return ""

    if hasattr(value, "value"):
        return str(value.value)

    return str(value)


def _contains_any(text: str, keywords: list[str]) -> bool:
    """Case-insensitive keyword matching without NLP."""

    text = text.lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


def _get_category(db: Session, issue: Issue) -> str:
    """Retrieve the issue category safely from the database."""

    category_id = getattr(issue, "category_id", None)

    print("CATEGORY ID:", category_id)

    if category_id is None:
        return "Unknown"

    try:
        category = (
            db.query(BugCategory)
            .filter(
                BugCategory.category_id == int(category_id)
            )
            .first()
        )

        if category is not None:
            category_name = getattr(
                category,
                "category_name",
                None
            )

            if category_name:
                print("CATEGORY FOUND:", category_name)
                return str(category_name)

        print("CATEGORY NOT FOUND:", category_id)

    except (TypeError, ValueError) as exc:
        print("CATEGORY LOOKUP ERROR:", exc)

    return "Unknown"


# ============================================================
# RESOLUTION RULES
# ============================================================

def _database_connection():
    return {
        "rule": "DATABASE / CONNECTION",
        "analysis": (
            "The issue appears to involve database or server "
            "connectivity. Check database availability, host and "
            "port configuration, credentials, network access, "
            "and connection settings."
        ),
        "resolution": (
            "Verify that the database server is running. Check the "
            "configured host, port, database name, and credentials. "
            "Inspect the backend connection error and correct the "
            "configuration or connectivity problem."
        ),
        "steps": [
            "Reproduce the connection failure.",
            "Verify that PostgreSQL or the required server is running.",
            "Check the configured host and port.",
            "Verify the database name and username.",
            "Check credentials without exposing passwords in logs.",
            "Inspect backend logs for the exact connection error.",
            "Retest the operation after correcting the problem."
        ],
        "prevention": (
            "Use database health checks, connection monitoring, "
            "configuration validation, and automated connectivity tests."
        )
    }


def _database_query():
    return {
        "rule": "DATABASE / SQL",
        "analysis": (
            "The issue appears to involve an SQL query or database "
            "operation. The likely investigation areas are query "
            "syntax, parameters, schema, and database constraints."
        ),
        "resolution": (
            "Inspect the failing SQL operation and its parameters. "
            "Verify the tables, columns, data types, and constraints. "
            "Correct the query or database operation and retest it."
        ),
        "steps": [
            "Reproduce the database operation.",
            "Inspect the failing SQL statement and error message.",
            "Verify table and column names.",
            "Check parameters, data types, and constraints.",
            "Correct the query or database operation.",
            "Run database integration tests."
        ],
        "prevention": (
            "Use SQL validation, schema migration checks, and "
            "database integration tests."
        )
    }


def _database_general():
    return {
        "rule": "DATABASE",
        "analysis": (
            "The issue appears to affect database functionality. "
            "Investigate database operations, transactions, schema, "
            "data integrity, and backend database handling."
        ),
        "resolution": (
            "Identify the affected database operation. Inspect the "
            "database logs, schema, transaction handling, and data. "
            "Correct the failing operation and verify the result."
        ),
        "steps": [
            "Reproduce the database issue.",
            "Inspect backend and database logs.",
            "Identify the affected database operation.",
            "Check the schema and data constraints.",
            "Correct the failing database operation.",
            "Retest the affected workflow."
        ],
        "prevention": (
            "Use database integration tests, schema validation, "
            "transaction handling, and monitoring."
        )
    }


def _authentication_login():
    return {
        "rule": "AUTHENTICATION / LOGIN",
        "analysis": (
            "The issue appears to affect the login process. "
            "Investigate credential validation, password verification, "
            "the login request, and the authentication response."
        ),
        "resolution": (
            "Inspect the login request and backend authentication flow. "
            "Verify that credentials reach the backend correctly and "
            "that password verification and error handling work as intended."
        ),
        "steps": [
            "Reproduce the login failure.",
            "Inspect the login request and response.",
            "Check backend credential validation.",
            "Verify password hashing and password verification.",
            "Inspect authentication errors in the backend logs.",
            "Retest login with valid and invalid credentials."
        ],
        "prevention": (
            "Use automated login tests, secure password handling, "
            "input validation, and authentication regression tests."
        )
    }


def _authentication_token():
    return {
        "rule": "AUTHENTICATION / JWT",
        "analysis": (
            "The issue appears to involve JWT or authentication-token "
            "handling. Investigate token creation, expiration, signature "
            "validation, storage, and transmission."
        ),
        "resolution": (
            "Inspect the token creation and validation flow. Verify "
            "expiration and signature settings, and confirm that the "
            "client sends the required Authorization header."
        ),
        "steps": [
            "Reproduce the token-related failure.",
            "Inspect the Authorization header.",
            "Check token generation and required claims.",
            "Verify expiration and signature validation.",
            "Inspect the protected API response.",
            "Retest with a valid token and an expired token."
        ],
        "prevention": (
            "Use consistent token validation, secure token handling, "
            "appropriate expiration, and protected-endpoint tests."
        )
    }


def _authentication_authorization():
    return {
        "rule": "AUTHENTICATION / AUTHORIZATION",
        "analysis": (
            "The issue appears to involve identity verification or "
            "access permissions. Investigate the authenticated user, "
            "role assignments, and authorization checks."
        ),
        "resolution": (
            "Trace the authentication and authorization flow. Verify "
            "the current user's identity, assigned role, required "
            "permissions, and access-control rules."
        ),
        "steps": [
            "Reproduce the access failure.",
            "Verify the authenticated user.",
            "Inspect the assigned role and permissions.",
            "Check the protected endpoint's access rules.",
            "Retest using accounts with the expected permissions."
        ],
        "prevention": (
            "Use centralized RBAC rules, authorization tests, and "
            "security logging."
        )
    }


def _frontend_button():
    return {
        "rule": "FRONTEND / BUTTON",
        "analysis": (
            "The issue appears to involve a button or user interaction. "
            "Investigate its event handler, JavaScript function, "
            "and any API request triggered by the action."
        ),
        "resolution": (
            "Inspect the button's event handler and related JavaScript. "
            "Check browser console errors and the network request. "
            "Correct the failing interaction and verify the result."
        ),
        "steps": [
            "Reproduce the button failure.",
            "Inspect browser console errors.",
            "Verify the button event handler.",
            "Check the JavaScript function.",
            "Inspect any API request and response.",
            "Retest the interaction."
        ],
        "prevention": (
            "Use UI interaction tests, JavaScript error handling, "
            "and frontend regression tests."
        )
    }


def _frontend_responsive():
    return {
        "rule": "FRONTEND / RESPONSIVE",
        "analysis": (
            "The issue appears to involve responsive layout behavior. "
            "Investigate CSS breakpoints, viewport sizing, overflowing "
            "elements, and mobile-specific styles."
        ),
        "resolution": (
            "Inspect the affected HTML elements and CSS media queries. "
            "Correct the layout, sizing, or responsive styles and test "
            "the page across different viewport sizes."
        ),
        "steps": [
            "Reproduce the issue at the affected screen size.",
            "Inspect the affected HTML elements.",
            "Check CSS media queries and breakpoints.",
            "Inspect overflow, width, and alignment rules.",
            "Correct the responsive styles.",
            "Test mobile, tablet, and desktop layouts."
        ],
        "prevention": (
            "Use responsive design checks and UI regression tests "
            "across multiple viewport sizes."
        )
    }


def _frontend_general():
    return {
        "rule": "FRONTEND / UI",
        "analysis": (
            "The issue appears to affect the frontend interface. "
            "Investigate the relevant HTML, CSS, JavaScript, browser "
            "behavior, and affected UI component."
        ),
        "resolution": (
            "Reproduce the interface problem and inspect the affected "
            "component. Identify the incorrect rendering or interaction, "
            "correct the responsible frontend code, and verify the result."
        ),
        "steps": [
            "Reproduce the issue in the browser.",
            "Inspect browser console errors.",
            "Check the affected HTML and CSS.",
            "Inspect related JavaScript behavior.",
            "Check API requests if the component uses the backend.",
            "Retest the interface."
        ],
        "prevention": (
            "Use UI validation, browser testing, and frontend regression tests."
        )
    }


def _backend_server_error():
    return {
        "rule": "BACKEND / SERVER ERROR",
        "analysis": (
            "The issue appears to involve a backend server error. "
            "Investigate the failing endpoint, request processing, "
            "exception traceback, and related database operations."
        ),
        "resolution": (
            "Reproduce the failing request and inspect the FastAPI "
            "logs and traceback. Identify the operation causing the "
            "exception, correct the backend logic, and retest the endpoint."
        ),
        "steps": [
            "Reproduce the failing API request.",
            "Inspect FastAPI logs and the traceback.",
            "Identify the failing function or operation.",
            "Check request validation and database operations.",
            "Correct the backend logic or error handling.",
            "Retest valid and invalid request scenarios."
        ],
        "prevention": (
            "Use API tests, input validation, structured logging, "
            "exception handling, and backend monitoring."
        )
    }


def _backend_not_found():
    return {
        "rule": "BACKEND / 404",
        "analysis": (
            "The issue appears to involve a missing API endpoint or "
            "resource. Investigate the URL, HTTP method, router registration, "
            "and requested resource identifier."
        ),
        "resolution": (
            "Verify the URL and HTTP method. Check FastAPI router "
            "registration and confirm that the requested resource exists. "
            "Correct the route or resource lookup as required."
        ),
        "steps": [
            "Reproduce the 404 response.",
            "Verify the requested URL and HTTP method.",
            "Check FastAPI route registration.",
            "Verify the requested resource identifier.",
            "Check whether the resource exists.",
            "Retest the endpoint."
        ],
        "prevention": (
            "Use API integration tests, route documentation, and "
            "resource-lookup regression tests."
        )
    }


def _backend_general():
    return {
        "rule": "BACKEND / API",
        "analysis": (
            "The issue appears to involve backend or API processing. "
            "Investigate request data, validation, endpoint logic, "
            "authentication, database interaction, and the response."
        ),
        "resolution": (
            "Trace the request through the affected API endpoint. "
            "Inspect validation, backend processing, and database "
            "operations. Correct the failing step and verify the response."
        ),
        "steps": [
            "Reproduce the API request.",
            "Inspect the request payload and HTTP status.",
            "Check authentication and input validation.",
            "Inspect endpoint logic and backend logs.",
            "Verify any database operations.",
            "Retest the API endpoint."
        ],
        "prevention": (
            "Use API validation, exception handling, automated endpoint "
            "tests, and backend monitoring."
        )
    }


def _performance():
    return {
        "rule": "PERFORMANCE",
        "analysis": (
            "The issue appears to involve application performance. "
            "Investigate response time, resource usage, database queries, "
            "and expensive backend or frontend operations."
        ),
        "resolution": (
            "Measure the affected operation, identify the performance "
            "bottleneck, optimize the responsible component, and measure "
            "the result again."
        ),
        "steps": [
            "Reproduce the performance issue.",
            "Measure response time and resource usage.",
            "Inspect slow database queries.",
            "Profile backend or frontend processing.",
            "Optimize the identified bottleneck.",
            "Compare performance before and after the change."
        ],
        "prevention": (
            "Use performance monitoring, profiling, query optimization, "
            "and load testing."
        )
    }


def _validation():
    return {
        "rule": "FUNCTIONAL / VALIDATION",
        "analysis": (
            "The issue appears to involve input validation or incorrect "
            "handling of data. Investigate input values, validation rules, "
            "error messages, and the affected workflow."
        ),
        "resolution": (
            "Reproduce the validation failure, inspect the input and "
            "validation rules, correct the responsible logic, and verify "
            "both valid and invalid inputs."
        ),
        "steps": [
            "Reproduce the validation problem.",
            "Identify the input that triggers the failure.",
            "Inspect frontend and backend validation rules.",
            "Check error messages and boundary conditions.",
            "Correct the validation logic.",
            "Test valid, invalid, and boundary inputs."
        ],
        "prevention": (
            "Use centralized validation, boundary testing, and automated "
            "negative test cases."
        )
    }


def _generic_functional(title: str):
    return {
        "rule": "GENERIC FUNCTIONAL",
        "analysis": (
            f"The issue '{title or 'Untitled issue'}' requires "
            "investigation of its reported behavior. Compare actual "
            "and expected results to identify the affected component."
        ),
        "resolution": (
            "Reproduce the reported behavior, compare actual and expected "
            "results, trace the affected workflow, correct the responsible "
            "component, and verify the complete workflow."
        ),
        "steps": [
            "Review the issue title and description.",
            "Reproduce the reported behavior.",
            "Compare actual and expected results.",
            "Trace the affected component.",
            "Identify the root cause and apply a correction.",
            "Retest the complete workflow."
        ],
        "prevention": (
            "Add regression tests for the reported scenario and include "
            "the affected workflow in future testing."
        )
    }


# ============================================================
# MAIN RESOLUTION ASSISTANCE FUNCTION
# ============================================================

def generate_resolution_assistance(
    db: Session,
    issue: Issue
) -> dict:
    """
    Generate deterministic, issue-specific resolution guidance.

    No NLP or machine learning is used.
    """

    issue_id = getattr(issue, "id", None)
    issue_key = getattr(issue, "issue_key", None)

    title = str(getattr(issue, "title", "") or "")
    description = str(getattr(issue, "description", "") or "")

    severity = _get_enum_value(
        getattr(issue, "severity", None)
    )

    priority = _get_enum_value(
        getattr(issue, "priority", None)
    )

    issue_type = _get_enum_value(
        getattr(issue, "issue_type", None)
    )

    category = _get_category(db, issue)
    category_lower = category.lower()

    issue_text = f"{title} {description}".lower()

    print("\n==============================================")
    print("BUGFLOW RESOLUTION DEBUG")
    print("Issue ID:", issue_id)
    print("Issue Key:", issue_key)
    print("Title:", title)
    print("Category:", category)
    print("Severity:", severity)
    print("Priority:", priority)
    print("Issue Type:", issue_type)
    print("Issue Text:", issue_text)
    print("==============================================")

    # --------------------------------------------------------
    # Determine the category family.
    # Specific categories take precedence over general keywords.
    # --------------------------------------------------------

    database_category = (
        "database" in category_lower
        or category_lower.strip() == "db"
    )

    auth_category = any(
        word in category_lower
        for word in [
            "authentication",
            "authorization",
            "login",
            "security",
            "access control"
        ]
    )

    frontend_category = any(
        word in category_lower
        for word in [
            "frontend",
            "front end",
            "user interface",
            "ui"
        ]
    )

    backend_category = any(
        word in category_lower
        for word in [
            "backend",
            "back end",
            "api"
        ]
    )

    performance_category = "performance" in category_lower

    # --------------------------------------------------------
    # 1. DATABASE
    # --------------------------------------------------------

    if database_category or _contains_any(
        issue_text,
        [
            "postgres",
            "postgresql",
            "database connection",
            "database server",
            "database down",
            "unable to connect to database",
            "cannot connect to database",
            "could not connect to database",
            "foreign key",
            "sql query",
            "database query"
        ]
    ):

        if _contains_any(
            issue_text,
            [
                "connection refused",
                "connection failed",
                "connection failure",
                "unable to connect",
                "cannot connect",
                "could not connect",
                "database down",
                "server unavailable",
                "host unreachable",
                "connection timeout"
            ]
        ):
            result = _database_connection()

        elif _contains_any(
            issue_text,
            [
                "query",
                "sql",
                "select statement",
                "insert statement",
                "update statement",
                "delete statement",
                "foreign key",
                "constraint violation"
            ]
        ):
            result = _database_query()

        else:
            result = _database_general()

    # --------------------------------------------------------
    # 2. AUTHENTICATION AND AUTHORIZATION
    # --------------------------------------------------------

    elif auth_category or _contains_any(
        issue_text,
        [
            "login",
            "log in",
            "sign in",
            "signin",
            "password",
            "jwt",
            "token",
            "unauthorized",
            "forbidden",
            "authentication",
            "authorization",
            "access denied",
            "permission denied"
        ]
    ):

        if _contains_any(
            issue_text,
            [
                "jwt",
                "token",
                "expired token",
                "invalid token"
            ]
        ):
            result = _authentication_token()

        elif _contains_any(
            issue_text,
            [
                "login",
                "log in",
                "sign in",
                "signin",
                "password"
            ]
        ):
            result = _authentication_login()

        else:
            result = _authentication_authorization()

    # --------------------------------------------------------
    # 3. FRONTEND
    # --------------------------------------------------------

    elif frontend_category or _contains_any(
        issue_text,
        [
            "button not working",
            "button does not work",
            "onclick",
            "css layout",
            "javascript error",
            "responsive layout",
            "mobile layout",
            "alignment issue",
            "dropdown not working",
            "sidebar not working",
            "page layout"
        ]
    ):

        if _contains_any(
            issue_text,
            [
                "mobile",
                "responsive",
                "phone screen",
                "screen size",
                "media query"
            ]
        ):
            result = _frontend_responsive()

        elif _contains_any(
            issue_text,
            [
                "button",
                "click",
                "onclick",
                "dropdown",
                "sidebar not working"
            ]
        ):
            result = _frontend_button()

        else:
            result = _frontend_general()

    # --------------------------------------------------------
    # 4. BACKEND / API
    # --------------------------------------------------------

    elif backend_category or _contains_any(
        issue_text,
        [
            "fastapi",
            "api endpoint",
            "endpoint error",
            "internal server error",
            "http 500",
            "http 404",
            "api request",
            "api response"
        ]
    ):

        if _contains_any(
            issue_text,
            [
                "internal server error",
                "http 500",
                "status code 500",
                "server error"
            ]
        ):
            result = _backend_server_error()

        elif _contains_any(
            issue_text,
            [
                "http 404",
                "status code 404",
                "missing endpoint",
                "endpoint not found"
            ]
        ):
            result = _backend_not_found()

        else:
            result = _backend_general()

    # --------------------------------------------------------
    # 5. PERFORMANCE
    # --------------------------------------------------------

    elif performance_category or _contains_any(
        issue_text,
        [
            "slow response",
            "response time",
            "latency",
            "performance issue",
            "loading slowly",
            "application is slow",
            "request timeout",
            "page is slow"
        ]
    ):
        result = _performance()

    # --------------------------------------------------------
    # 6. FUNCTIONAL VALIDATION
    # --------------------------------------------------------

    elif _contains_any(
        issue_text,
        [
            "validation",
            "invalid input",
            "incorrect error message",
            "form validation",
            "required field",
            "invalid data"
        ]
    ):
        result = _validation()

    # --------------------------------------------------------
    # 7. DEFAULT FUNCTIONAL ISSUE
    # --------------------------------------------------------

    else:
        result = _generic_functional(title)

    # --------------------------------------------------------
    # Add issue-specific context to the returned result.
    # --------------------------------------------------------

    analysis = (
        f"{result['analysis']} "
        f"Issue ID: {issue_id}. "
        f"Category: {category}. "
        f"Severity: {severity or 'Not specified'}. "
        f"Priority: {priority or 'Not specified'}."
    )

    final_result = {
        "issue_id": issue_id,
        "issue_key": issue_key,
        "category": category,
        "severity": severity,
        "priority": priority,
        "analysis": analysis,
        "resolution": result["resolution"],
        "steps": result["steps"],
        "prevention": result["prevention"]
    }

    print("SELECTED RESOLUTION RULE:", result["rule"])
    print("ISSUE ID:", issue_id)
    print("RESOLUTION:", result["resolution"])
    print("==============================================\n")

    return final_result
